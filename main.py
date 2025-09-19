#!/usr/bin/env python3
"""
GestureBeats Studio - Main Application Launcher
A comprehensive music creation application using hand gestures.
"""

import sys
import os
import subprocess
import argparse
import time
import threading
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        ('streamlit', 'streamlit'),
        ('opencv-python', 'cv2'),
        ('mediapipe', 'mediapipe'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('plotly', 'plotly'),
        ('websockets', 'websockets')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def start_websocket_bridge():
    """Start the WebSocket bridge in a separate process"""
    try:
        from websocket_bridge import GestureBeatsBridge
        bridge = GestureBeatsBridge()
        bridge.start()
        return bridge
    except Exception as e:
        print(f"❌ Failed to start WebSocket bridge: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start frontend: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped by user")

def start_analytics():
    """Start the analytics dashboard"""
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "analysis_dashboard.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start analytics: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Analytics dashboard stopped by user")

def run_gesture_detection():
    """Run gesture detection standalone"""
    try:
        from gesture import GestureDetector
        detector = GestureDetector()
        detector.start_websocket_server()
        
        import cv2
        cap = cv2.VideoCapture(0)
        
        print("🎥 Gesture detection started! Press 'q' to quit.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            annotated_frame, hand_info = detector.process_frame(frame)
            cv2.imshow('GestureBeats Studio - Gesture Detection', annotated_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        detector.cleanup()
        
    except Exception as e:
        print(f"❌ Gesture detection error: {e}")

def run_music_generator():
    """Run music generator standalone"""
    try:
        from music_generator import MusicGenerator
        generator = MusicGenerator()
        
        print("🎵 Music generator started!")
        print("This is a test run - no real-time input.")
        
        # Test with sample data
        test_hand_info = {
            'left': {'gesture': 'peace', 'confidence': 0.8},
            'right': {'gesture': 'fist', 'confidence': 0.9}
        }
        
        music_events = generator.process_gesture(test_hand_info)
        print(f"Generated {len(music_events)} music events")
        
        # Test recording
        generator.start_recording()
        time.sleep(2)
        result = generator.stop_recording()
        
        if result:
            print(f"Test recording saved: {result}")
        
        stats = generator.get_session_stats()
        print(f"Session stats: {stats}")
        
    except Exception as e:
        print(f"❌ Music generator error: {e}")

def create_directories():
    """Create necessary directories"""
    directories = ['sessions', 'recordings', 'exports']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

def main():
    """Main application launcher"""
    parser = argparse.ArgumentParser(
        description="GestureBeats Studio - Music Creation with Hand Gestures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start full application
  python main.py --frontend         # Start only frontend
  python main.py --analytics        # Start only analytics dashboard
  python main.py --gesture          # Run gesture detection only
  python main.py --music            # Run music generator only
  python main.py --check-deps       # Check dependencies only
        """
    )
    
    parser.add_argument('--frontend', action='store_true', 
                       help='Start only the Streamlit frontend')
    parser.add_argument('--analytics', action='store_true', 
                       help='Start only the analytics dashboard')
    parser.add_argument('--gesture', action='store_true', 
                       help='Run gesture detection standalone')
    parser.add_argument('--music', action='store_true', 
                       help='Run music generator standalone')
    parser.add_argument('--check-deps', action='store_true', 
                       help='Check dependencies and exit')
    parser.add_argument('--no-bridge', action='store_true', 
                       help='Start frontend without WebSocket bridge')
    
    args = parser.parse_args()
    
    print("🎵 GestureBeats Studio - Music Creation with Hand Gestures")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    if args.check_deps:
        print("✅ Dependency check complete!")
        sys.exit(0)
    
    # Create necessary directories
    create_directories()
    
    # Handle different modes
    if args.gesture:
        print("\n🎥 Starting gesture detection...")
        run_gesture_detection()
        
    elif args.music:
        print("\n🎵 Starting music generator...")
        run_music_generator()
        
    elif args.analytics:
        print("\n📊 Starting analytics dashboard...")
        start_analytics()
        
    elif args.frontend:
        print("\n🌐 Starting frontend...")
        if not args.no_bridge:
            print("🔗 Starting WebSocket bridge...")
            bridge = start_websocket_bridge()
            if bridge:
                time.sleep(2)  # Give bridge time to start
        start_frontend()
        
    else:
        # Full application mode
        print("\n🚀 Starting full GestureBeats Studio application...")
        
        # Start WebSocket bridge
        print("🔗 Starting WebSocket bridge...")
        bridge = start_websocket_bridge()
        if not bridge:
            print("⚠️  WebSocket bridge failed to start. Continuing without real-time features...")
        
        # Give bridge time to start
        time.sleep(2)
        
        # Start frontend
        print("🌐 Starting frontend...")
        try:
            start_frontend()
        except KeyboardInterrupt:
            print("\n🛑 Application stopped by user")
        finally:
            if bridge:
                bridge.stop()

if __name__ == "__main__":
    main()
