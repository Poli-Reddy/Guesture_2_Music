import json
import wave
import numpy as np
import time
import os
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import cv2
import base64
from collections import deque
import asyncio
import websockets

class SessionRecorder:
    """Enhanced session recording system with video, audio, and metadata"""
    
    def __init__(self, output_dir="sessions"):
        self.output_dir = output_dir
        self.is_recording = False
        self.session_id = None
        self.start_time = None
        
        # Recording data
        self.audio_data = []
        self.video_frames = []
        self.gesture_data = []
        self.music_events = []
        self.metadata = {}
        
        # Threading
        self.recording_thread = None
        self.stop_event = threading.Event()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Video recording settings
        self.video_fps = 30
        self.video_codec = cv2.VideoWriter_fourcc(*'mp4v')
        
    def start_recording(self, session_name=None):
        """Start recording a new session"""
        if self.is_recording:
            return False
        
        if session_name:
            session_name = os.path.basename(session_name)
        self.session_id = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = time.time()
        self.is_recording = True
        
        # Reset data
        self.audio_data = []
        self.video_frames = []
        self.gesture_data = []
        self.music_events = []
        self.metadata = {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'duration': 0,
            'total_events': 0,
            'instruments_used': set(),
            'gestures_used': set()
        }
        
        # Start recording thread
        self.stop_event.clear()
        self.recording_thread = threading.Thread(target=self._recording_loop)
        self.recording_thread.start()
        
        print(f"Recording started: {self.session_id}")
        return True
    
    def stop_recording(self):
        """Stop recording and save session"""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        self.stop_event.set()
        
        if self.recording_thread:
            self.recording_thread.join(timeout=5)
        
        # Calculate final metadata
        end_time = time.time()
        self.metadata['duration'] = end_time - self.start_time
        self.metadata['end_time'] = end_time
        self.metadata['total_events'] = len(self.music_events)
        self.metadata['instruments_used'] = list(self.metadata['instruments_used'])
        self.metadata['gestures_used'] = list(self.metadata['gestures_used'])
        
        # Save session files
        session_files = self._save_session()
        
        print(f"Recording stopped: {self.session_id}")
        print(f"Duration: {self.metadata['duration']:.2f} seconds")
        print(f"Events: {self.metadata['total_events']}")
        
        return session_files
    
    def _recording_loop(self):
        """Main recording loop"""
        while not self.stop_event.is_set():
            time.sleep(0.033)  # ~30 FPS
    
    def add_audio_data(self, audio_data: np.ndarray):
        """Add audio data to recording"""
        if self.is_recording and audio_data is not None:
            self.audio_data.append(audio_data.copy())
    
    def add_video_frame(self, frame: np.ndarray):
        """Add video frame to recording"""
        if self.is_recording and frame is not None:
            # Compress frame for storage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.video_frames.append(frame_rgb.copy())
    
    def add_gesture_data(self, gesture_data: Dict[str, Any]):
        """Add gesture data to recording"""
        if self.is_recording and gesture_data:
            timestamp = time.time() - self.start_time
            self.gesture_data.append({
                'timestamp': timestamp,
                'data': gesture_data
            })
    
    def add_music_event(self, music_event: Dict[str, Any]):
        """Add music event to recording"""
        if self.is_recording and music_event:
            timestamp = time.time() - self.start_time
            event_data = {
                'timestamp': timestamp,
                'data': music_event
            }
            self.music_events.append(event_data)
            
            # Update metadata
            if 'instrument' in music_event:
                self.metadata['instruments_used'].add(music_event['instrument'])
            if 'gesture' in music_event:
                self.metadata['gestures_used'].add(music_event['gesture'])
    
    def _save_session(self):
        """Save session data to files"""
        session_files = {}
        
        try:
            # Save audio
            if self.audio_data:
                audio_file = os.path.join(self.output_dir, f"{self.session_id}_audio.wav")
                self._save_audio_file(audio_file)
                session_files['audio'] = audio_file
            
            # Save video
            if self.video_frames:
                video_file = os.path.join(self.output_dir, f"{self.session_id}_video.mp4")
                self._save_video_file(video_file)
                session_files['video'] = video_file
            
            # Save gesture data
            gesture_file = os.path.join(self.output_dir, f"{self.session_id}_gestures.json")
            self._save_gesture_data(gesture_file)
            session_files['gestures'] = gesture_file
            
            # Save music events
            music_file = os.path.join(self.output_dir, f"{self.session_id}_music.json")
            self._save_music_events(music_file)
            session_files['music'] = music_file
            
            # Save metadata
            metadata_file = os.path.join(self.output_dir, f"{self.session_id}_metadata.json")
            self._save_metadata(metadata_file)
            session_files['metadata'] = metadata_file
            
            # Save complete session
            session_file = os.path.join(self.output_dir, f"{self.session_id}_session.json")
            self._save_complete_session(session_file)
            session_files['session'] = session_file
            
        except Exception as e:
            print(f"Error saving session: {e}")
        
        return session_files
    
    def _save_audio_file(self, filename: str):
        """Save audio data as WAV file"""
        if not self.audio_data:
            return
        
        # Combine all audio data
        combined_audio = np.concatenate(self.audio_data, axis=0)
        
        # Normalize audio
        combined_audio = np.clip(combined_audio, -1.0, 1.0)
        
        # Convert to 16-bit PCM
        audio_16bit = (combined_audio * 32767).astype(np.int16)
        
        # Save as WAV
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(44100)  # 44.1 kHz
            wav_file.writeframes(audio_16bit.tobytes())
    
    def _save_video_file(self, filename: str):
        """Save video frames as MP4 file"""
        if not self.video_frames:
            return
        
        # Get frame dimensions
        height, width, channels = self.video_frames[0].shape
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filename, fourcc, self.video_fps, (width, height))
        
        # Write frames
        for frame in self.video_frames:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
        
        out.release()
    
    def _save_gesture_data(self, filename: str):
        """Save gesture data as JSON"""
        with open(filename, 'w') as f:
            json.dump(self.gesture_data, f, indent=2)
    
    def _save_music_events(self, filename: str):
        """Save music events as JSON"""
        with open(filename, 'w') as f:
            json.dump(self.music_events, f, indent=2)
    
    def _save_metadata(self, filename: str):
        """Save session metadata as JSON"""
        with open(filename, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _save_complete_session(self, filename: str):
        """Save complete session data as JSON"""
        session_data = {
            'metadata': self.metadata,
            'gesture_data': self.gesture_data,
            'music_events': self.music_events,
            'audio_duration': len(self.audio_data) / 44100 if self.audio_data else 0,
            'video_frames': len(self.video_frames),
            'recording_quality': {
                'audio_sample_rate': 44100,
                'audio_channels': 2,
                'video_fps': self.video_fps,
                'video_codec': 'mp4v'
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2)

class SessionPlayer:
    """Session playback system with synchronized audio, video, and gesture visualization"""
    
    def __init__(self, session_file: str):
        self.session_file = os.path.basename(session_file)
        self.session_data = None
        self.is_playing = False
        self.current_time = 0
        self.playback_speed = 1.0
        
        # Playback components
        self.audio_player = None
        self.video_player = None
        self.gesture_visualizer = None
        
        # Threading
        self.playback_thread = None
        self.stop_event = threading.Event()
        
    def load_session(self):
        """Load session data from file"""
        try:
            with open(self.session_file, 'r') as f:
                self.session_data = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False
    
    def play(self, start_time=0, speed=1.0):
        """Start playing the session"""
        if not self.session_data:
            if not self.load_session():
                return False
        
        self.current_time = start_time
        self.playback_speed = speed
        self.is_playing = True
        self.stop_event.clear()
        
        # Start playback thread
        self.playback_thread = threading.Thread(target=self._playback_loop)
        self.playback_thread.start()
        
        return True
    
    def pause(self):
        """Pause playback"""
        self.is_playing = False
    
    def resume(self):
        """Resume playback"""
        self.is_playing = True
    
    def stop(self):
        """Stop playback"""
        self.is_playing = False
        self.stop_event.set()
        
        if self.playback_thread:
            self.playback_thread.join(timeout=2)
    
    def seek(self, time_position):
        """Seek to specific time position"""
        self.current_time = max(0, min(time_position, self.get_duration()))
    
    def set_speed(self, speed):
        """Set playback speed"""
        self.playback_speed = max(0.1, min(5.0, speed))
    
    def get_duration(self):
        """Get total session duration"""
        if self.session_data:
            return self.session_data['metadata']['duration']
        return 0
    
    def get_current_time(self):
        """Get current playback time"""
        return self.current_time
    
    def _playback_loop(self):
        """Main playback loop"""
        start_time = time.time()
        
        while not self.stop_event.is_set() and self.current_time < self.get_duration():
            if self.is_playing:
                # Calculate current time
                elapsed = (time.time() - start_time) * self.playback_speed
                self.current_time = elapsed
                
                # Process events at current time
                self._process_events_at_time(self.current_time)
                
                # Small delay to prevent overwhelming
                time.sleep(0.016)  # ~60 FPS
            else:
                time.sleep(0.1)
    
    def _process_events_at_time(self, current_time):
        """Process events that should occur at the current time"""
        # Process music events
        for event in self.session_data.get('music_events', []):
            event_time = event['timestamp']
            if abs(event_time - current_time) < 0.1:  # Within 100ms tolerance
                self._play_music_event(event['data'])
        
        # Process gesture events
        for gesture in self.session_data.get('gesture_data', []):
            gesture_time = gesture['timestamp']
            if abs(gesture_time - current_time) < 0.1:
                self._visualize_gesture(gesture['data'])
    
    def _play_music_event(self, music_event):
        """Play a music event"""
        # This would integrate with the music generator
        print(f"Playing music event: {music_event}")
    
    def _visualize_gesture(self, gesture_data):
        """Visualize a gesture event"""
        # This would update the gesture visualization
        print(f"Visualizing gesture: {gesture_data}")

class SessionManager:
    """Manage multiple sessions and provide analysis"""
    
    def __init__(self, sessions_dir="sessions"):
        self.sessions_dir = sessions_dir
        self.sessions = {}
        self._load_sessions()
    
    def _load_sessions(self):
        """Load all available sessions"""
        if not os.path.exists(self.sessions_dir):
            return
        
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith('_session.json'):
                session_id = filename.replace('_session.json', '')
                session_file = os.path.join(self.sessions_dir, filename)
                
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    self.sessions[session_id] = session_data
                except Exception as e:
                    print(f"Error loading session {session_id}: {e}")
    
    def get_session_list(self):
        """Get list of available sessions"""
        return list(self.sessions.keys())
    
    def get_session_info(self, session_id):
        """Get information about a specific session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['metadata']
        return None
    
    def get_session_stats(self, session_id):
        """Get statistics for a specific session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        metadata = session['metadata']
        
        # Calculate additional statistics
        music_events = session.get('music_events', [])
        gesture_data = session.get('gesture_data', [])
        
        # Gesture frequency
        gesture_counts = {}
        for gesture in gesture_data:
            if 'data' in gesture and 'gestures' in gesture['data']:
                for hand, info in gesture['data']['gestures'].items():
                    if info and 'gesture' in info:
                        gesture_name = info['gesture']
                        gesture_counts[gesture_name] = gesture_counts.get(gesture_name, 0) + 1
        
        # Hand usage
        hand_usage = {'left': 0, 'right': 0}
        for event in music_events:
            if 'data' in event and 'hand' in event['data']:
                hand = event['data']['hand']
                hand_usage[hand] += 1
        
        # Tempo analysis
        if len(music_events) > 1:
            time_span = music_events[-1]['timestamp'] - music_events[0]['timestamp']
            events_per_second = len(music_events) / time_span if time_span > 0 else 0
            estimated_bpm = events_per_second * 60
        else:
            estimated_bpm = 0
        
        # Complexity score
        unique_combinations = set()
        for event in music_events:
            if 'data' in event:
                data = event['data']
                if 'gesture' in data and 'instrument' in data:
                    unique_combinations.add((data['gesture'], data['instrument']))
        
        complexity_score = len(unique_combinations) / len(music_events) if music_events else 0
        
        return {
            'session_id': session_id,
            'duration': metadata.get('duration', 0),
            'total_events': metadata.get('total_events', 0),
            'gesture_counts': gesture_counts,
            'hand_usage': hand_usage,
            'estimated_bpm': estimated_bpm,
            'complexity_score': complexity_score,
            'instruments_used': metadata.get('instruments_used', []),
            'gestures_used': metadata.get('gestures_used', [])
        }
    
    def get_all_stats(self):
        """Get statistics for all sessions"""
        all_stats = {}
        for session_id in self.sessions:
            all_stats[session_id] = self.get_session_stats(session_id)
        return all_stats
    
    def delete_session(self, session_id):
        """Delete a session and its files"""
        if session_id not in self.sessions:
            return False
        
        session_id = os.path.basename(session_id)
        try:
            # Delete all session files
            for filename in os.listdir(self.sessions_dir):
                if filename.startswith(session_id):
                    filepath = os.path.join(self.sessions_dir, filename)
                    os.remove(filepath)
            
            # Remove from sessions dict
            del self.sessions[session_id]
            return True
            
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def export_session(self, session_id, export_format='json'):
        """Export session in specified format"""
        if session_id not in self.sessions:
            return None
        
        session_data = self.sessions[session_id]
        
        if export_format == 'json':
            return json.dumps(session_data, indent=2)
        elif export_format == 'csv':
            # Export music events as CSV
            music_events = session_data.get('music_events', [])
            if not music_events:
                return None
            
            csv_data = "timestamp,hand,instrument,gesture,note\n"
            for event in music_events:
                data = event.get('data', {})
                
                def sanitize_csv_value(value):
                    value = str(value)
                    if value.startswith(('=', '+', '-', '@')):
                        return "'" + value
                    return value

                timestamp = sanitize_csv_value(event['timestamp'])
                hand = sanitize_csv_value(data.get('hand', ''))
                instrument = sanitize_csv_value(data.get('instrument', ''))
                gesture = sanitize_csv_value(data.get('gesture', ''))
                note = sanitize_csv_value(data.get('note', ''))

                csv_data += f"{timestamp},{hand},{instrument},{gesture},{note}\n"
            
            return csv_data
        
        return None

# Example usage
if __name__ == "__main__":
    # Test session recorder
    recorder = SessionRecorder()
    
    # Start recording
    recorder.start_recording("test_session")
    
    # Simulate some data
    for i in range(100):
        # Simulate audio data
        audio_data = np.random.randn(1000, 2) * 0.1
        recorder.add_audio_data(audio_data)
        
        # Simulate gesture data
        gesture_data = {
            'left': {'gesture': 'peace', 'confidence': 0.8},
            'right': {'gesture': 'fist', 'confidence': 0.9}
        }
        recorder.add_gesture_data(gesture_data)
        
        # Simulate music event
        music_event = {
            'hand': 'left',
            'instrument': 'piano',
            'gesture': 'peace',
            'note': 'C4'
        }
        recorder.add_music_event(music_event)
        
        time.sleep(0.1)
    
    # Stop recording
    session_files = recorder.stop_recording()
    print(f"Session saved: {session_files}")
    
    # Test session manager
    manager = SessionManager()
    sessions = manager.get_session_list()
    print(f"Available sessions: {sessions}")
    
    if sessions:
        stats = manager.get_session_stats(sessions[0])
        print(f"Session stats: {stats}")
