import cv2
import mediapipe as mp
import numpy as np
import json
import time
import threading
import queue
from collections import deque
import asyncio
import websockets
import json

class GestureDetector:
    def __init__(self, confidence_threshold=0.7, smoothing_frames=5):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=confidence_threshold,
            min_tracking_confidence=0.5
        )
        
        self.confidence_threshold = confidence_threshold
        self.smoothing_frames = smoothing_frames
        self.gesture_history = deque(maxlen=smoothing_frames)
        
        # Gesture definitions
        self.gestures = {
            'peace': self._detect_peace,
            'fist': self._detect_fist,
            'open_palm': self._detect_open_palm,
            'thumbs_up': self._detect_thumbs_up,
            'rock_horn': self._detect_rock_horn,
            'pinch': self._detect_pinch
        }
        
        self.gesture_names = {
            'peace': '✌️ Peace',
            'fist': '✊ Fist',
            'open_palm': '✋ Open Palm',
            'thumbs_up': '👍 Thumbs Up',
            'rock_horn': '🤘 Rock Horn',
            'pinch': '🤏 Pinch'
        }
        
        self.current_gestures = {'left': None, 'right': None}
        self.gesture_confidence = {'left': 0.0, 'right': 0.0}
        
        # WebSocket server for real-time communication
        self.websocket_clients = set()
        self.websocket_server = None
        
    def _get_hand_landmarks(self, landmarks):
        """Convert MediaPipe landmarks to numpy array"""
        return np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
    
    def _calculate_distance(self, p1, p2):
        """Calculate Euclidean distance between two points"""
        return np.sqrt(np.sum((p1 - p2) ** 2))
    
    def _is_finger_extended(self, landmarks, finger_tips, finger_pips):
        """Check if a finger is extended based on landmark positions"""
        extended = []
        for tip, pip in zip(finger_tips, finger_pips):
            # Check if tip is higher than pip (considering y-axis is inverted)
            if landmarks[tip][1] < landmarks[pip][1]:
                extended.append(True)
            else:
                extended.append(False)
        return extended
    
    def _detect_peace(self, landmarks):
        """Detect peace sign (index and middle finger extended)"""
        # Landmark indices for finger tips and PIPs
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        finger_pips = [3, 6, 10, 14, 18]  # PIP joints
        
        extended = self._is_finger_extended(landmarks, finger_tips, finger_pips)
        
        # Peace sign: index and middle extended, others not
        if extended[1] and extended[2] and not extended[0] and not extended[3] and not extended[4]:
            return 0.9
        return 0.0
    
    def _detect_fist(self, landmarks):
        """Detect closed fist (all fingers curled)"""
        finger_tips = [4, 8, 12, 16, 20]
        finger_pips = [3, 6, 10, 14, 18]
        
        extended = self._is_finger_extended(landmarks, finger_tips, finger_pips)
        
        # Fist: no fingers extended
        if not any(extended):
            return 0.9
        return 0.0
    
    def _detect_open_palm(self, landmarks):
        """Detect open palm (all fingers extended)"""
        finger_tips = [4, 8, 12, 16, 20]
        finger_pips = [3, 6, 10, 14, 18]
        
        extended = self._is_finger_extended(landmarks, finger_tips, finger_pips)
        
        # Open palm: all fingers extended
        if all(extended):
            return 0.9
        return 0.0
    
    def _detect_thumbs_up(self, landmarks):
        """Detect thumbs up (only thumb extended)"""
        finger_tips = [4, 8, 12, 16, 20]
        finger_pips = [3, 6, 10, 14, 18]
        
        extended = self._is_finger_extended(landmarks, finger_tips, finger_pips)
        
        # Thumbs up: only thumb extended
        if extended[0] and not any(extended[1:]):
            return 0.9
        return 0.0
    
    def _detect_rock_horn(self, landmarks):
        """Detect rock horn (index and pinky extended)"""
        finger_tips = [4, 8, 12, 16, 20]
        finger_pips = [3, 6, 10, 14, 18]
        
        extended = self._is_finger_extended(landmarks, finger_tips, finger_pips)
        
        # Rock horn: index and pinky extended, others not
        if extended[1] and extended[4] and not extended[0] and not extended[2] and not extended[3]:
            return 0.9
        return 0.0
    
    def _detect_pinch(self, landmarks):
        """Detect pinch gesture (thumb and index finger close together)"""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        distance = self._calculate_distance(thumb_tip, index_tip)
        
        # Pinch: thumb and index very close
        if distance < 0.05:  # Threshold for pinch detection
            return 0.9
        return 0.0
    
    def _detect_gesture(self, landmarks):
        """Detect the most likely gesture from landmarks"""
        best_gesture = None
        best_confidence = 0.0
        
        for gesture_name, detector_func in self.gestures.items():
            confidence = detector_func(landmarks)
            if confidence > best_confidence:
                best_confidence = confidence
                best_gesture = gesture_name
        
        return best_gesture, best_confidence
    
    def _smooth_gesture(self, gesture, confidence):
        """Apply smoothing to prevent gesture flickering"""
        self.gesture_history.append((gesture, confidence))
        
        if len(self.gesture_history) < self.smoothing_frames:
            return gesture, confidence
        
        # Count occurrences of each gesture in recent history
        gesture_counts = {}
        for g, c in self.gesture_history:
            if g is not None:
                gesture_counts[g] = gesture_counts.get(g, 0) + 1
        
        if not gesture_counts:
            return None, 0.0
        
        # Return most frequent gesture
        most_common = max(gesture_counts, key=gesture_counts.get)
        avg_confidence = np.mean([c for g, c in self.gesture_history if g == most_common])
        
        return most_common, avg_confidence
    
    def process_frame(self, frame):
        """Process a single frame and return annotated frame with gesture info"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        annotated_frame = frame.copy()
        hand_info = {'left': None, 'right': None}
        
        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Determine hand label (left/right)
                hand_label = results.multi_handedness[idx].classification[0].label.lower()
                
                # Draw hand landmarks
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # Get landmarks as numpy array
                landmarks = self._get_hand_landmarks(hand_landmarks)
                
                # Detect gesture
                gesture, confidence = self._detect_gesture(landmarks)
                gesture, confidence = self._smooth_gesture(gesture, confidence)
                
                if confidence >= self.confidence_threshold:
                    self.current_gestures[hand_label] = gesture
                    self.gesture_confidence[hand_label] = confidence
                    
                    # Draw gesture label
                    h, w, c = annotated_frame.shape
                    x = int(hand_landmarks.landmark[0].x * w)
                    y = int(hand_landmarks.landmark[0].y * h) - 20
                    
                    gesture_text = f"{hand_label.title()}: {self.gesture_names.get(gesture, 'Unknown')} ({confidence:.2f})"
                    cv2.putText(annotated_frame, gesture_text, (x, y), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Draw bounding box
                    x_coords = [int(lm.x * w) for lm in hand_landmarks.landmark]
                    y_coords = [int(lm.y * h) for lm in hand_landmarks.landmark]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    
                    cv2.rectangle(annotated_frame, (x_min-10, y_min-10), 
                                (x_max+10, y_max+10), (0, 255, 0), 2)
                    
                    hand_info[hand_label] = {
                        'gesture': gesture,
                        'confidence': confidence,
                        'landmarks': landmarks.tolist()
                    }
                else:
                    self.current_gestures[hand_label] = None
                    self.gesture_confidence[hand_label] = 0.0
        
        return annotated_frame, hand_info
    
    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections for real-time gesture streaming"""
        self.websocket_clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.websocket_clients.remove(websocket)
    
    async def broadcast_gestures(self, hand_info):
        """Broadcast gesture information to all connected clients"""
        if self.websocket_clients:
            message = json.dumps({
                'timestamp': time.time(),
                'gestures': hand_info,
                'current_gestures': self.current_gestures,
                'confidence': self.gesture_confidence
            })
            
            disconnected = set()
            for client in self.websocket_clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            
            self.websocket_clients -= disconnected
    
    def start_websocket_server(self, host='localhost', port=8765):
        """Start WebSocket server for real-time communication"""
        async def server():
            self.websocket_server = await websockets.serve(
                self.websocket_handler, host, port
            )
            print(f"WebSocket server started on ws://{host}:{port}")
            await self.websocket_server.wait_closed()
        
        # Run server in a separate thread
        server_thread = threading.Thread(target=lambda: asyncio.run(server()))
        server_thread.daemon = True
        server_thread.start()
    
    def get_current_gestures(self):
        """Get current gesture state"""
        return {
            'gestures': self.current_gestures,
            'confidence': self.gesture_confidence
        }
    
    def cleanup(self):
        """Clean up resources"""
        if self.hands:
            self.hands.close()
        if self.websocket_server:
            self.websocket_server.close()

# Example usage and testing
if __name__ == "__main__":
    detector = GestureDetector()
    detector.start_websocket_server()
    
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            annotated_frame, hand_info = detector.process_frame(frame)
            
            # Display the frame
            cv2.imshow('GestureBeats Studio - Gesture Detection', annotated_frame)
            
            # Print current gestures
            if hand_info['left'] or hand_info['right']:
                print(f"Gestures: {hand_info}")
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.cleanup()
