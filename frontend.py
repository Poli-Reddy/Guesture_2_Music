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

# JavaScript for real-time audio and animations
AUDIO_JS = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script>
<script>
    // Initialize Tone.js
    Tone.start();
    
    // Create audio context and instruments
    const instruments = {
        piano: new Tone.Sampler({
            urls: {
                "C4": "https://tonejs.github.io/audio/casio/C4.mp3",
                "D4": "https://tonejs.github.io/audio/casio/D4.mp3",
                "E4": "https://tonejs.github.io/audio/casio/E4.mp3",
                "F4": "https://tonejs.github.io/audio/casio/F4.mp3",
                "G4": "https://tonejs.github.io/audio/casio/G4.mp3",
                "A4": "https://tonejs.github.io/audio/casio/A4.mp3",
                "B4": "https://tonejs.github.io/audio/casio/B4.mp3",
                "C5": "https://tonejs.github.io/audio/casio/C5.mp3"
            }
        }).toDestination(),
        
        guitar: new Tone.Sampler({
            urls: {
                "E2": "https://tonejs.github.io/audio/guitar/E2.mp3",
                "A2": "https://tonejs.github.io/audio/guitar/A2.mp3",
                "D3": "https://tonejs.github.io/audio/guitar/D3.mp3",
                "G3": "https://tonejs.github.io/audio/guitar/G3.mp3",
                "B3": "https://tonejs.github.io/audio/guitar/B3.mp3",
                "E4": "https://tonejs.github.io/audio/guitar/E4.mp3"
            }
        }).toDestination(),
        
        drums: new Tone.Player({
            url: "https://tonejs.github.io/audio/drum-samples/kick.mp3"
        }).toDestination(),
        
        violin: new Tone.Sampler({
            urls: {
                "G3": "https://tonejs.github.io/audio/violin/G3.mp3",
                "D4": "https://tonejs.github.io/audio/violin/D4.mp3",
                "A4": "https://tonejs.github.io/audio/violin/A4.mp3",
                "E5": "https://tonejs.github.io/audio/violin/E5.mp3"
            }
        }).toDestination(),
        
        flute: new Tone.Sampler({
            urls: {
                "C5": "https://tonejs.github.io/audio/flute/C5.mp3",
                "D5": "https://tonejs.github.io/audio/flute/D5.mp3",
                "E5": "https://tonejs.github.io/audio/flute/E5.mp3",
                "F5": "https://tonejs.github.io/audio/flute/F5.mp3",
                "G5": "https://tonejs.github.io/audio/flute/G5.mp3",
                "A5": "https://tonejs.github.io/audio/flute/A5.mp3",
                "B5": "https://tonejs.github.io/audio/flute/B5.mp3",
                "C6": "https://tonejs.github.io/audio/flute/C6.mp3"
            }
        }).toDestination(),
        
        saxophone: new Tone.Sampler({
            urls: {
                "Bb3": "https://tonejs.github.io/audio/saxophone/Bb3.mp3",
                "C4": "https://tonejs.github.io/audio/saxophone/C4.mp3",
                "D4": "https://tonejs.github.io/audio/saxophone/D4.mp3",
                "F4": "https://tonejs.github.io/audio/saxophone/F4.mp3",
                "G4": "https://tonejs.github.io/audio/saxophone/G4.mp3",
                "A4": "https://tonejs.github.io/audio/saxophone/A4.mp3",
                "Bb4": "https://tonejs.github.io/audio/saxophone/Bb4.mp3",
                "C5": "https://tonejs.github.io/audio/saxophone/C5.mp3"
            }
        }).toDestination()
    };
    
    // Gesture to note mapping
    const gestureMapping = {
        'peace': 0,
        'fist': 1,
        'open_palm': 2,
        'thumbs_up': 3,
        'rock_horn': 4,
        'pinch': 5
    };
    
    // Note arrays for each instrument
    const instrumentNotes = {
        piano: ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5'],
        guitar: ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
        drums: ['kick', 'snare', 'hihat', 'crash', 'tom1', 'tom2'],
        violin: ['G3', 'D4', 'A4', 'E5'],
        flute: ['C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5', 'C6'],
        saxophone: ['Bb3', 'C4', 'D4', 'F4', 'G4', 'A4', 'Bb4', 'C5']
    };
    
    // Play note function
    function playNote(instrument, gesture, hand) {
        const noteIndex = gestureMapping[gesture] || 0;
        const notes = instrumentNotes[instrument];
        const note = notes[noteIndex % notes.length];
        
        if (instrument === 'drums') {
            // Play drum sound
            instruments.drums.start();
        } else {
            // Play melodic instrument
            instruments[instrument].triggerAttackRelease(note, "8n");
        }
        
        // Visual feedback
        showNoteVisualization(note, hand);
    }
    
    // Show note visualization
    function showNoteVisualization(note, hand) {
        const container = document.getElementById('note-visualization');
        if (container) {
            const noteElement = document.createElement('div');
            noteElement.className = 'note-bubble';
            noteElement.textContent = note;
            noteElement.style.cssText = `
                position: absolute;
                ${hand === 'left' ? 'left: 20px;' : 'right: 20px;'}
                top: 50%;
                transform: translateY(-50%);
                background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
                color: white;
                padding: 10px 15px;
                border-radius: 25px;
                font-weight: bold;
                animation: noteFloat 2s ease-out forwards;
                z-index: 1000;
            `;
            
            container.appendChild(noteElement);
            
            setTimeout(() => {
                if (noteElement.parentNode) {
                    noteElement.parentNode.removeChild(noteElement);
                }
            }, 2000);
        }
    }
    
    // Add CSS for note animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes noteFloat {
            0% { opacity: 1; transform: translateY(-50%) scale(0.5); }
            50% { opacity: 1; transform: translateY(-100px) scale(1.2); }
            100% { opacity: 0; transform: translateY(-200px) scale(0.8); }
        }
    `;
    document.head.appendChild(style);
    
    // WebSocket connection for real-time gesture data
    let ws = null;
    function connectWebSocket() {
        ws = new WebSocket('ws://localhost:8765');
        
        ws.onopen = function() {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.gestures) {
                // Process gesture data and play notes
                for (const [hand, info] of Object.entries(data.gestures)) {
                    if (info && info.gesture && info.confidence > 0.7) {
                        const instrument = hand === 'left' ? 'piano' : 'guitar'; // Default instruments
                        playNote(instrument, info.gesture, hand);
                    }
                }
            }
        };
        
        ws.onclose = function() {
            console.log('WebSocket disconnected');
            setTimeout(connectWebSocket, 1000); // Reconnect after 1 second
        };
    }
    
    // Connect when page loads
    connectWebSocket();
</script>
"""

class GestureBeatsFrontend:
    def __init__(self):
        self.gesture_detector = GestureDetector()
        self.music_generator = MusicGenerator()
        self.video_queue = queue.Queue(maxsize=10)
        self.is_running = False
        
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="🎵 GestureBeats Studio",
            page_icon="🎵",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Inject custom CSS
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        
        # Inject JavaScript for audio
        st.markdown(AUDIO_JS, unsafe_allow_html=True)
    
    def create_header(self):
        """Create animated header"""
        st.markdown("""
        <div class="gesture-container" style="text-align: center; margin-bottom: 30px;">
            <h1 style="font-family: 'Orbitron', monospace; font-size: 3em; font-weight: 900; 
                       color: #00ffff; text-shadow: 0 0 20px #00ffff; margin: 0;">
                🎵 GestureBeats Studio 🎵
            </h1>
            <p style="font-size: 1.2em; color: #ffffff; margin: 10px 0;">
                Create music with your hands • Real-time gesture recognition • 6 instruments
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def create_video_section(self):
        """Create video display section with real-time gesture detection"""
        st.markdown("### 🎥 Live Camera Feed")
        
        # Create video container
        video_placeholder = st.empty()
        
        # Add note visualization container
        st.markdown('<div id="note-visualization" style="position: relative; height: 100px;"></div>', 
                   unsafe_allow_html=True)
        
        # Camera controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎬 Start Camera", key="start_camera"):
                self.start_camera()
        
        with col2:
            if st.button("⏹️ Stop Camera", key="stop_camera"):
                self.stop_camera()
        
        with col3:
            camera_status = "🟢 Running" if self.is_running else "🔴 Stopped"
            st.markdown(f"**Status:** {camera_status}")
        
        # Video processing loop
        if self.is_running:
            self.process_video_feed(video_placeholder)
    
    def start_camera(self):
        """Start camera capture"""
        self.is_running = True
        # Start audio playback
        self.music_generator.start_audio_playback()
        st.success("Camera started! Make gestures to create music!")
    
    def stop_camera(self):
        """Stop camera capture"""
        self.is_running = False
        # Stop audio playback
        self.music_generator.stop_audio_playback()
        st.info("Camera stopped.")
    
    def process_video_feed(self, placeholder):
        """Process video feed with gesture detection"""
        cap = cv2.VideoCapture(0)
        
        # Set camera properties for consistent frame size
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        try:
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    st.warning("Failed to read from camera. Please check camera connection.")
                    break
                
                # Ensure frame has correct dimensions
                if frame is None or frame.size == 0:
                    continue
                
                # Process frame for gesture detection
                try:
                    annotated_frame, hand_info = self.gesture_detector.process_frame(frame)
                    
                    # Process music generation with error handling
                    try:
                        music_events = self.music_generator.process_gesture(hand_info)
                    except Exception as music_error:
                        st.warning(f"Music generation error: {music_error}")
                        music_events = []
                    
                    # Convert frame for display
                    annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                    
                    # Display frame
                    placeholder.image(annotated_frame_rgb, channels="RGB", use_container_width=True)
                    
                except Exception as gesture_error:
                    st.warning(f"Gesture detection error: {gesture_error}")
                    # Display original frame if gesture detection fails
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                
                # Small delay to prevent overwhelming the UI
                time.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            st.error(f"Camera error: {e}")
        finally:
            cap.release()
    
    def create_instrument_controls(self):
        """Create instrument selection and control panels"""
        st.markdown("### 🎛️ Instrument Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🖐️ Left Hand")
            left_instrument = st.selectbox(
                "Select Instrument",
                options=list(self.music_generator.instruments.keys()),
                format_func=lambda x: self.music_generator.instruments[x]['name'],
                key="left_instrument"
            )
            
            left_volume = st.slider(
                "Volume", 0.0, 1.0, 0.7, 0.1,
                key="left_volume"
            )
            
            self.music_generator.set_instrument('left', left_instrument)
            self.music_generator.set_volume('left', left_volume)
        
        with col2:
            st.markdown("#### 🖐️ Right Hand")
            right_instrument = st.selectbox(
                "Select Instrument",
                options=list(self.music_generator.instruments.keys()),
                format_func=lambda x: self.music_generator.instruments[x]['name'],
                key="right_instrument"
            )
            
            right_volume = st.slider(
                "Volume", 0.0, 1.0, 0.7, 0.1,
                key="right_volume"
            )
            
            self.music_generator.set_instrument('right', right_instrument)
            self.music_generator.set_volume('right', right_volume)
    
    def create_audio_controls(self):
        """Create audio effect and tempo controls"""
        st.markdown("### 🎚️ Audio Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🎵 Tempo")
            tempo = st.slider(
                "BPM", 60, 200, 120, 5,
                key="tempo"
            )
            self.music_generator.set_tempo(tempo)
        
        with col2:
            st.markdown("#### 🎛️ Effects")
            reverb = st.checkbox("Reverb", key="reverb")
            delay = st.checkbox("Delay", key="delay")
            distortion = st.checkbox("Distortion", key="distortion")
            
            self.music_generator.set_effect('reverb', reverb)
            self.music_generator.set_effect('delay', delay)
            self.music_generator.set_effect('distortion', distortion)
        
        with col3:
            st.markdown("#### 🎤 Sensitivity")
            sensitivity = st.slider(
                "Gesture Sensitivity", 0.5, 0.9, 0.7, 0.05,
                key="sensitivity"
            )
            self.gesture_detector.confidence_threshold = sensitivity
    
    def create_recording_section(self):
        """Create recording and playback controls"""
        st.markdown("### 🎙️ Recording & Playback")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔴 Start Recording", key="start_recording"):
                self.music_generator.start_recording()
                st.success("Recording started!")
        
        with col2:
            if st.button("⏹️ Stop Recording", key="stop_recording"):
                result = self.music_generator.stop_recording()
                if result:
                    st.success(f"Session saved: {result[0]}")
                else:
                    st.warning("No audio data to save")
        
        with col3:
            recording_status = "🔴 Recording" if self.music_generator.is_recording else "⏹️ Stopped"
            st.markdown(f"**Status:** {recording_status}")
    
    def create_analysis_dashboard(self):
        """Create music analysis dashboard"""
        st.markdown("### 📊 Music Analysis")
        
        # Get session statistics
        stats = self.music_generator.get_session_stats()
        
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
            
            # Gesture frequency chart
            if stats.get('gesture_counts'):
                st.markdown("#### Gesture Frequency")
                gesture_data = stats['gesture_counts']
                
                fig = px.bar(
                    x=list(gesture_data.keys()),
                    y=list(gesture_data.values()),
                    title="Gesture Usage",
                    color=list(gesture_data.values()),
                    color_continuous_scale="viridis"
                )
                fig.update_layout(
                    xaxis_title="Gesture",
                    yaxis_title="Count",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Hand usage pie chart
            if stats.get('hand_usage'):
                st.markdown("#### Hand Usage Distribution")
                hand_data = stats['hand_usage']
                
                fig = px.pie(
                    values=list(hand_data.values()),
                    names=list(hand_data.keys()),
                    title="Left vs Right Hand Usage"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("No session data available. Start recording to see analysis!")
    
    def create_tutorial_section(self):
        """Create interactive tutorial section"""
        st.markdown("### 🎓 Interactive Tutorials")
        
        tutorial_options = [
            "Piano Basics",
            "Guitar Rhythms", 
            "Drum Patterns",
            "String Ensemble"
        ]
        
        selected_tutorial = st.selectbox(
            "Select Tutorial",
            tutorial_options,
            key="tutorial_select"
        )
        
        if selected_tutorial == "Piano Basics":
            st.markdown("""
            #### 🎹 Piano Basics Tutorial
            - **Peace ✌️**: Play C4 note
            - **Fist ✊**: Play D4 note  
            - **Open Palm ✋**: Play E4 note
            - **Thumbs Up 👍**: Play F4 note
            - **Rock Horn 🤘**: Play G4 note
            - **Pinch 🤏**: Play A4 note
            
            Try making these gestures with your left hand to play piano notes!
            """)
        
        elif selected_tutorial == "Guitar Rhythms":
            st.markdown("""
            #### 🎸 Guitar Rhythms Tutorial
            - **Peace ✌️**: Play E2 (low E string)
            - **Fist ✊**: Play A2 (A string)
            - **Open Palm ✋**: Play D3 (D string)
            - **Thumbs Up 👍**: Play G3 (G string)
            - **Rock Horn 🤘**: Play B3 (B string)
            - **Pinch 🤏**: Play E4 (high E string)
            
            Use your right hand to strum different guitar strings!
            """)
        
        elif selected_tutorial == "Drum Patterns":
            st.markdown("""
            #### 🥁 Drum Patterns Tutorial
            - **Peace ✌️**: Kick drum
            - **Fist ✊**: Snare drum
            - **Open Palm ✋**: Hi-hat
            - **Thumbs Up 👍**: Crash cymbal
            - **Rock Horn 🤘**: Tom 1
            - **Pinch 🤏**: Tom 2
            
            Create drum patterns with both hands!
            """)
        
        elif selected_tutorial == "String Ensemble":
            st.markdown("""
            #### 🎻 String Ensemble Tutorial
            - **Left Hand**: Violin (G3, D4, A4, E5)
            - **Right Hand**: Cello (C3, G3, D4, A4)
            
            Use both hands to create beautiful string harmonies!
            """)
    
    def run(self):
        """Main application runner"""
        self.setup_page_config()
        self.create_header()
        
        # Sidebar controls
        with st.sidebar:
            st.markdown("### 🎛️ Control Panel")
            self.create_instrument_controls()
            st.markdown("---")
            self.create_audio_controls()
            st.markdown("---")
            self.create_recording_section()
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.create_video_section()
        
        with col2:
            self.create_tutorial_section()
        
        # Analysis dashboard
        st.markdown("---")
        self.create_analysis_dashboard()
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 50px; color: #ffffff; opacity: 0.7;">
            <p>🎵 GestureBeats Studio - Create music with your hands 🎵</p>
            <p>Powered by MediaPipe, Tone.js, and Streamlit</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main function to run the application"""
    app = GestureBeatsFrontend()
    app.run()

if __name__ == "__main__":
    main()
