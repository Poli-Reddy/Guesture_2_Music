import streamlit as st
import cv2
import numpy as np
import json
import time
import threading
import queue
import asyncio
import websockets
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import base64
from gesture import GestureDetector
from music_generator import MusicGenerator
import streamlit.components.v1 as components
import os

# Custom CSS for advanced animations and styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .gesture-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .video-container {
        position: relative;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); }
        50% { box-shadow: 0 15px 40px rgba(0, 255, 255, 0.3); }
    }
    
    .gesture-label {
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        font-size: 1.2em;
        color: #00ffff;
        text-shadow: 0 0 10px #00ffff;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff; }
        to { text-shadow: 0 0 20px #00ffff, 0 0 30px #00ffff, 0 0 40px #00ffff; }
    }
    
    .instrument-panel {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        color: white;
        font-weight: bold;
        text-align: center;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .control-panel {
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 15px;
        padding: 20px;
        color: white;
        text-align: center;
        margin: 10px 0;
        animation: fadeInUp 0.6s ease-out;
    }
    
    @keyframes fadeInUp {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .recording-indicator {
        animation: blink 1s infinite;
        color: #ff4444;
        font-weight: bold;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    .confidence-meter {
        background: linear-gradient(90deg, #ff4444, #ffaa00, #00ff00);
        height: 10px;
        border-radius: 5px;
        margin: 5px 0;
        position: relative;
        overflow: hidden;
    }
    
    .confidence-fill {
        height: 100%;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 5px;
        transition: width 0.3s ease;
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { background-position: -200px 0; }
        100% { background-position: 200px 0; }
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
    }
</style>
"""

class GestureBeatsFrontend:
    def __init__(self):
        self.websocket_uri = "ws://localhost:8765"
        if 'gesture_detector' not in st.session_state:
            st.session_state.gesture_detector = GestureDetector()
        self.gesture_detector = st.session_state.gesture_detector

        if 'music_generator' not in st.session_state:
            st.session_state.music_generator = MusicGenerator()
        self.music_generator = st.session_state.music_generator

        if 'is_running' not in st.session_state:
            st.session_state.is_running = False
        if 'is_recording' not in st.session_state:
            st.session_state.is_recording = False

        # Video processing thread
        self.video_thread = None
        self.video_queue = queue.Queue(maxsize=10)
        self.stop_video = threading.Event()

    async def _send_websocket_message(self, message_type, data={}):
        try:
            async with websockets.connect(self.websocket_uri) as websocket:
                message = {
                    "type": message_type,
                    "data": data
                }
                await websocket.send(json.dumps(message))
        except Exception as e:
            st.error(f"Failed to send websocket message: {e}")

    def send_websocket_message(self, message_type, data={}):
        # Use asyncio.run only if no event loop is running
        try:
            asyncio.get_running_loop()
            # If there's a running loop, create a task
            asyncio.create_task(self._send_websocket_message(message_type, data))
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            asyncio.run(self._send_websocket_message(message_type, data))
        
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="🎵 GestureBeats Studio",
            page_icon="🎵",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    def create_header(self):
        """Create animated header"""
        st.markdown("""
        <div class="gesture-container" style="text-align: center; margin-bottom: 30px;">
            <h1 style="font-family: 'Orbitron', monospace; font-size: 3em; font-weight: 900;
                       color: #00ffff; text-shadow: 0 0 20px #00ffff; margin: 0;">
                🎵 GestureBeats Studio 🎵
            </h1>
            <p style="font-size: 1.2em; color: #ffffff; margin: 10px 0;">
                Create music with your hands • Real-time gesture recognition • 6 instruments at the left corner menu
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def create_video_section(self):
        """Create video display section with real-time gesture detection"""
        st.markdown("### 🎥 Live Camera Feed")

        # Camera size adjustment
        camera_size = st.slider("Camera Size", 0.3, 1.0, 0.6, 0.1, key="camera_size")

        video_placeholder = st.empty()

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🎬 Start Camera", key="start_camera"):
                st.session_state.is_running = True
                self.start_video_thread()

        with col2:
            if st.button("⏹️ Stop Camera", key="stop_camera"):
                st.session_state.is_running = False
                self.stop_video_thread()
                if st.session_state.is_recording:
                    self.music_generator.stop_recording()
                    st.session_state.is_recording = False
                    st.success("Recording stopped. Check playlist for saved audio.")

        with col3:
            camera_status = "🟢 Running" if st.session_state.is_running else "🔴 Stopped"
            st.markdown(f"**Status:** {camera_status}")

        if st.session_state.is_running:
            self.update_video_feed(video_placeholder, camera_size)
    
    def start_video_thread(self):
        """Start video processing in a separate thread"""
        if self.video_thread and self.video_thread.is_alive():
            return

        self.stop_video.clear()
        self.video_thread = threading.Thread(target=self._video_processing_loop, daemon=True)
        self.video_thread.start()

    def stop_video_thread(self):
        """Stop video processing thread"""
        self.stop_video.set()
        if self.video_thread:
            self.video_thread.join(timeout=2)

    def _video_processing_loop(self):
        """Video processing loop running in separate thread"""
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        try:
            while not self.stop_video.is_set():
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                annotated_frame, hand_info = self.gesture_detector.process_frame(frame)

                if hand_info.get('left') or hand_info.get('right'):
                    self.send_websocket_message("gesture_data", hand_info)
                    # Process gestures for music generation
                    self.music_generator.process_gesture(hand_info)

                # Put frame in queue for UI update
                try:
                    self.video_queue.put_nowait(annotated_frame)
                except queue.Full:
                    # Remove old frame if queue is full
                    try:
                        self.video_queue.get_nowait()
                        self.video_queue.put_nowait(annotated_frame)
                    except queue.Empty:
                        pass

                time.sleep(0.033)  # ~30 FPS
        finally:
            cap.release()

    def update_video_feed(self, placeholder, camera_size=0.6):
        """Update video feed from queue"""
        try:
            frame = self.video_queue.get_nowait()
            # Resize frame based on camera_size
            height, width = frame.shape[:2]
            new_width = int(width * camera_size)
            new_height = int(height * camera_size)
            resized_frame = cv2.resize(frame, (new_width, new_height))
            placeholder.image(resized_frame, channels="BGR", use_container_width=False)
        except queue.Empty:
            pass

    def create_instrument_controls(self):
        """Create instrument selection and control panels"""
        with st.expander("🎛️ Instrument Controls", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🖐️ Left Hand")
                left_instrument = st.selectbox(
                    "Select Instrument",
                    options=['piano', 'guitar', 'drums', 'violin', 'flute', 'saxophone'],
                    key="left_instrument"
                )
                self.music_generator.set_instrument("left", left_instrument)

                left_volume = st.slider("Volume", 0.0, 1.0, 0.7, 0.1, key="left_volume")
                self.music_generator.set_volume("left", left_volume)

            with col2:
                st.markdown("#### 🖐️ Right Hand")
                right_instrument = st.selectbox(
                    "Select Instrument",
                    options=['piano', 'guitar', 'drums', 'violin', 'flute', 'saxophone'],
                    key="right_instrument"
                )
                self.music_generator.set_instrument("right", right_instrument)

                right_volume = st.slider("Volume", 0.0, 1.0, 0.7, 0.1, key="right_volume")
                self.music_generator.set_volume("right", right_volume)
    
    def create_audio_controls(self):
        """Create audio effect and tempo controls"""
        with st.expander("🎚️ Audio Controls", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🎵 Tempo")
                tempo = st.slider("BPM", 60, 200, 120, 5, key="tempo")
                self.music_generator.set_tempo(tempo)
            
            with col2:
                st.markdown("#### 🎛️ Effects")
                reverb = st.checkbox("Reverb", key="reverb")
                self.music_generator.set_effect("reverb", reverb)
                delay = st.checkbox("Delay", key="delay")
                self.music_generator.set_effect("delay", delay)
                distortion = st.checkbox("Distortion", key="distortion")
                self.music_generator.set_effect("distortion", distortion)
            
            with col3:
                st.markdown("#### 🎤 Sensitivity")
                sensitivity = st.slider("Gesture Sensitivity", 0.5, 0.9, 0.7, 0.05, key="sensitivity")
                self.gesture_detector.confidence_threshold = sensitivity
    
    def create_recording_section(self):
        """Create recording and playback controls"""
        with st.expander("🎙️ Recording Controls", expanded=True):
            start_recording_disabled = not st.session_state.is_running or st.session_state.is_recording
            if st.button("🔴 Start Recording", key="start_recording", disabled=start_recording_disabled):
                self.music_generator.start_recording()
                st.session_state.is_recording = True
                st.success("Recording started!")

            if st.session_state.is_recording:
                if st.button("⏹️ Stop Recording", key="stop_recording"):
                    self.music_generator.stop_recording()
                    st.session_state.is_recording = False
                    st.success("Recording stopped. Check playlist for saved audio.")

            recording_status = "🔴 Recording" if st.session_state.is_recording else "⏹️ Stopped"
            st.markdown(f"**Status:** {recording_status}")

    def create_playlist_section(self):
        """Create a playlist of recorded audio files."""
        st.markdown("### 🎶 Your Recordings")
        
        recordings_dir = "recordings"
        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)
            
        audio_files = [f for f in os.listdir(recordings_dir) if f.endswith('.wav')]
        
        if st.button("🔄 Refresh Playlist"):
            pass
            
        if not audio_files:
            st.info("No recordings found yet. Start recording to create your first track!")
        else:
            for audio_file in sorted(audio_files, reverse=True):
                st.markdown(f"**{audio_file}**")
                audio_path = os.path.join(recordings_dir, audio_file)
                try:
                    with open(audio_path, 'rb') as f:
                        st.audio(f.read(), format='audio/wav')
                except Exception as e:
                    st.error(f"Could not play file {audio_file}. Error: {e}")

    def create_analysis_dashboard(self):
        """Create music analysis dashboard"""
        st.markdown("### 📊 Music Analysis")
        recordings_dir = "recordings"
        stats_files = [f for f in os.listdir(recordings_dir) if f.endswith('_stats.json')]

        if not stats_files:
            st.info("No analysis data found. Record a session to generate analysis.")
            return

        latest_stats_file = max(stats_files, key=lambda f: os.path.getmtime(os.path.join(recordings_dir, f)))
        
        with open(os.path.join(recordings_dir, latest_stats_file), 'r') as f:
            stats = json.load(f)
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Events", stats.get('total_events', 0))
            
            with col2:
                st.metric("Complexity Score", f"{stats.get('complexity_score', 0):.2f}")
            
            with col3:
                st.metric("Estimated BPM", f"{stats.get('estimated_bpm', 0):.1f}")
            
            with col4:
                left_usage = stats.get('hand_usage', {}).get('left', 0)
                right_usage = stats.get('hand_usage', {}).get('right', 0)
                total_usage = left_usage + right_usage
                if total_usage > 0:
                    left_percent = (left_usage / total_usage) * 100
                    st.metric("Left Hand Usage", f"{left_percent:.1f}%")
                else:
                    st.metric("Left Hand Usage", "0%")
            
            if stats.get('gesture_counts'):
                st.markdown("#### Gesture Frequency")
                gesture_data = stats['gesture_counts']
                
                fig = px.bar(x=list(gesture_data.keys()), y=list(gesture_data.values()), title="Gesture Usage")
                st.plotly_chart(fig, use_container_width=True)

    def create_tutorial_section(self):
        """Create interactive tutorial section"""
        with st.expander("🎓 Interactive Tutorials"):
            st.info("Tutorials are currently disabled.")

    def run(self):
        """Main application runner"""
        self.setup_page_config()
        self.create_header()
        
        with st.sidebar:
            st.markdown("## 🎛️ Control Panel (6 instruments)")
            self.create_instrument_controls()
            self.create_audio_controls()
            self.create_recording_section()
            self.create_tutorial_section()

        self.create_video_section()

        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            self.create_playlist_section()
        with col2:
            self.create_analysis_dashboard()
        
        st.markdown("---<div style='text-align: center; margin-top: 50px; color: #ffffff; opacity: 0.7;'><p>🎵 GestureBeats Studio - Create music with your hands 🎵</p><p>Powered by MediaPipe and Streamlit</p></div>", unsafe_allow_html=True)

def main():
    """Main function to run the application"""
    app = GestureBeatsFrontend()
    app.run()

if __name__ == "__main__":
    main()
