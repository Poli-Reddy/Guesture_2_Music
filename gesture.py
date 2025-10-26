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
        self.left_gesture_history = deque(maxlen=smoothing_frames)
        self.right_gesture_history = deque(maxlen=smoothing_frames)
        
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
    
    def _is_finger_extended(self, landmarks):
        """Check which fingers are extended with improved accuracy"""
        # Landmark indices for MediaPipe hand model
        # 0: wrist, 1-4: thumb, 5-8: index, 9-12: middle, 13-16: ring, 17-20: pinky
        
        extended_fingers = []
        
        # Thumb (special case - compare x-coordinates for horizontal extension)
        # Check if thumb tip is further from wrist than thumb IP joint
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]
        
        # For thumb, check horizontal distance from wrist center
        thumb_extended = abs(thumb_tip[0] - wrist[0]) > abs(thumb_ip[0] - wrist[0])
        extended_fingers.append(thumb_extended)
        
        # Other fingers (index, middle, ring, pinky)
        # Compare tip y-coordinate with PIP joint y-coordinate
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky tips
        finger_pips = [6, 10, 14, 18]  # Index, Middle, Ring, Pinky PIP joints
        finger_mcps = [5, 9, 13, 17]   # Index, Middle, Ring, Pinky MCP joints
        
        for tip_idx, pip_idx, mcp_idx in zip(finger_tips, finger_pips, finger_mcps):
            tip = landmarks[tip_idx]
            pip = landmarks[pip_idx]
            mcp = landmarks[mcp_idx]
            
            # Finger is extended if tip is above PIP and the angle is reasonable
            # Also check that tip is above MCP for better accuracy
            finger_extended = (tip[1] < pip[1]) and (tip[1] < mcp[1])
            
            # Additional check: ensure reasonable finger straightness
            # The tip should be reasonably aligned with the finger direction
            tip_to_pip_dist = self._calculate_distance(tip, pip)
            pip_to_mcp_dist = self._calculate_distance(pip, mcp)
            
            # If the distances are too small, finger might be curled
            if tip_to_pip_dist < 0.02 or pip_to_mcp_dist < 0.02:
                finger_extended = False
            
            extended_fingers.append(finger_extended)
        
        return extended_fingers
    
    def _detect_peace(self, landmarks):
        """Detect peace sign (index and middle finger extended, others folded)"""
        extended = self._is_finger_extended(landmarks)
        
        # Peace sign: index (1) and middle (2) extended, thumb (0), ring (3), pinky (4) not extended
        peace_pattern = not extended[0] and extended[1] and extended[2] and not extended[3] and not extended[4]
        
        if peace_pattern:
            # Additional verification: check finger separation
            index_tip = landmarks[8]
            middle_tip = landmarks[12]
            finger_separation = self._calculate_distance(index_tip, middle_tip)
            
            # Fingers should be reasonably separated for peace sign
            if 0.03 < finger_separation < 0.15:
                return 0.95
            else:
                return 0.7
        
        return 0.0
    
    def _detect_fist(self, landmarks):
        """Detect closed fist (all fingers curled)"""
        extended = self._is_finger_extended(landmarks)
        
        # Fist: no fingers should be extended
        if not any(extended):
            # Additional check: verify knuckles are higher than fingertips
            fingertips = [4, 8, 12, 16, 20]
            knuckles = [2, 5, 9, 13, 17]  # MCP joints
            
            fingers_curled = 0
            for tip_idx, knuckle_idx in zip(fingertips[1:], knuckles[1:]):  # Skip thumb
                if landmarks[knuckle_idx][1] < landmarks[tip_idx][1]:  # Knuckle higher than tip
                    fingers_curled += 1
            
            if fingers_curled >= 3:  # At least 3 fingers clearly curled
                return 0.95
            else:
                return 0.8
        
        # Partial fist (only thumb extended is still considered fist-like)
        elif extended[0] and not any(extended[1:]):
            return 0.6
        
        return 0.0
    
    def _detect_open_palm(self, landmarks):
        """Detect open palm (all fingers extended and spread)"""
        extended = self._is_finger_extended(landmarks)
        
        # Open palm: all fingers extended
        if all(extended):
            # Additional verification: check finger spread
            fingertips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
            finger_distances = []
            
            for i in range(len(fingertips) - 1):
                dist = self._calculate_distance(landmarks[fingertips[i]], landmarks[fingertips[i + 1]])
                finger_distances.append(dist)
            
            avg_separation = np.mean(finger_distances)
            
            # Fingers should be reasonably spread apart
            if avg_separation > 0.04:
                return 0.95
            else:
                return 0.75  # Fingers extended but not spread
        
        return 0.0
    
    def _detect_thumbs_up(self, landmarks):
        """Detect thumbs up (only thumb extended, others folded)"""
        extended = self._is_finger_extended(landmarks)
        
        # Thumbs up: only thumb extended, all others folded
        thumbs_up_pattern = extended[0] and not any(extended[1:])
        
        if thumbs_up_pattern:
            # Additional verification: thumb should be pointing upward
            thumb_tip = landmarks[4]
            thumb_mcp = landmarks[2]
            wrist = landmarks[0]
            
            # Thumb tip should be higher than thumb MCP and wrist
            thumb_upward = thumb_tip[1] < thumb_mcp[1] and thumb_tip[1] < wrist[1]
            
            # Check thumb angle - should be roughly vertical
            thumb_angle = abs(thumb_tip[0] - thumb_mcp[0]) / abs(thumb_tip[1] - thumb_mcp[1] + 0.001)
            
            if thumb_upward and thumb_angle < 1.0:  # More vertical than horizontal
                return 0.95
            else:
                return 0.7
        
        return 0.0
    
    def _detect_rock_horn(self, landmarks):
        """Detect rock horn (index and pinky extended, others folded)"""
        extended = self._is_finger_extended(landmarks)
        
        # Rock horn: index (1) and pinky (4) extended, thumb (0), middle (2), ring (3) folded
        rock_pattern = not extended[0] and extended[1] and not extended[2] and not extended[3] and extended[4]
        
        if rock_pattern:
            # Additional verification: check that middle and ring are clearly folded
            middle_tip = landmarks[12]
            ring_tip = landmarks[16]
            middle_pip = landmarks[10]
            ring_pip = landmarks[14]
            
            # Middle and ring tips should be below their PIP joints
            middle_folded = middle_tip[1] > middle_pip[1]
            ring_folded = ring_tip[1] > ring_pip[1]
            
            if middle_folded and ring_folded:
                return 0.95
            else:
                return 0.75
        
        return 0.0
    
    def _detect_pinch(self, landmarks):
        """Detect pinch gesture (thumb and index finger close together)"""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        distance = self._calculate_distance(thumb_tip, index_tip)
        
        # Check if other fingers are extended or folded
        extended = self._is_finger_extended(landmarks)
        
        # Pinch: thumb and index very close
        if distance < 0.04:  # Adjusted threshold for better accuracy
            # Better pinch if other fingers are extended (classic pinch gesture)
            if extended[2] and extended[3] and extended[4]:  # Middle, ring, pinky extended
                return 0.95
            # Still a pinch if other fingers are folded
            elif not extended[2] and not extended[3] and not extended[4]:
                return 0.85
            else:
                return 0.7
        elif distance < 0.06:  # Near pinch
            return 0.5
        
        return 0.0
    
    def _detect_gesture(self, landmarks):
        """Detect the most likely gesture from landmarks"""
        best_gesture = None
        best_confidence = 0.0
        
        for gesture_name, detector_func in self.gestures.items():
            confidence = detector_func(landmarks)
            if confidence > best_confidence and confidence > 0.5:  # Minimum confidence threshold
                best_confidence = confidence
                best_gesture = gesture_name
        
        return best_gesture, best_confidence
    
    def _smooth_gesture(self, gesture, confidence, hand_label):
        """Apply smoothing to prevent gesture flickering per hand"""
        if hand_label == 'left':
            history = self.left_gesture_history
        else:
            history = self.right_gesture_history

        history.append((gesture, confidence))

        if len(history) < self.smoothing_frames:
            return gesture, confidence

        # Count occurrences of each gesture in recent history with confidence weighting
        gesture_scores = {}
        for g, c in history:
            if g is not None and c > 0.5:
                gesture_scores[g] = gesture_scores.get(g, 0) + c

        if not gesture_scores:
            return None, 0.0

        # Return gesture with highest weighted score
        best_gesture = max(gesture_scores, key=gesture_scores.get)

        # Calculate average confidence for the best gesture
        confidence_values = [c for g, c in history if g == best_gesture]
        avg_confidence = np.mean(confidence_values) if confidence_values else 0.0

        # Only return if it appears in majority of recent frames
        gesture_count = sum(1 for g, c in history if g == best_gesture and c > 0.5)
        if gesture_count >= self.smoothing_frames // 2:
            return best_gesture, avg_confidence
        else:
            return None, 0.0
    
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
                gesture, confidence = self._smooth_gesture(gesture, confidence, hand_label)
                
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