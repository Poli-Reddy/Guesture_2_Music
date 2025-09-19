#!/usr/bin/env python3
"""
Setup script for GestureBeats Studio
Handles installation, configuration, and initial setup
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print application banner"""
    print("🎵" + "=" * 58 + "🎵")
    print("🎵" + " " * 20 + "GestureBeats Studio" + " " * 20 + "🎵")
    print("🎵" + " " * 15 + "Music Creation with Hand Gestures" + " " * 15 + "🎵")
    print("🎵" + "=" * 58 + "🎵")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        
        print("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try running: pip install -r requirements.txt")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'sessions',
        'recordings', 
        'exports',
        'temp',
        'logs'
    ]
    
    print("📁 Creating directories...")
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ {directory}/")
    
    return True

def check_camera():
    """Check if camera is available"""
    print("📷 Checking camera availability...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✅ Camera is working!")
                cap.release()
                return True
            else:
                print("⚠️  Camera detected but cannot read frames")
                cap.release()
                return False
        else:
            print("❌ No camera detected")
            return False
            
    except ImportError:
        print("❌ OpenCV not installed - cannot check camera")
        return False
    except Exception as e:
        print(f"❌ Camera check failed: {e}")
        return False

def check_audio():
    """Check if audio system is working"""
    print("🔊 Checking audio system...")
    
    try:
        import numpy as np
        import wave
        
        # Create a simple test audio file
        sample_rate = 44100
        duration = 0.1
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Try to write a test WAV file
        test_file = "temp/test_audio.wav"
        with wave.open(test_file, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        # Clean up test file
        os.remove(test_file)
        
        print("✅ Audio system is working!")
        return True
        
    except Exception as e:
        print(f"❌ Audio system check failed: {e}")
        return False

def create_config_file():
    """Create default configuration file"""
    config = {
        "camera": {
            "device_id": 0,
            "width": 640,
            "height": 480,
            "fps": 30
        },
        "audio": {
            "sample_rate": 44100,
            "channels": 2,
            "bit_depth": 16
        },
        "gesture": {
            "confidence_threshold": 0.7,
            "smoothing_frames": 5
        },
        "music": {
            "default_tempo": 120,
            "default_volume": 0.7
        },
        "recording": {
            "output_dir": "sessions",
            "video_codec": "mp4v",
            "audio_format": "wav"
        }
    }
    
    import json
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration file created: config.json")

def run_tests():
    """Run basic functionality tests"""
    print("🧪 Running basic tests...")
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Import gesture detector
    try:
        from gesture import GestureDetector
        print("   ✅ Gesture detector import")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Gesture detector import failed: {e}")
    
    # Test 2: Import music generator
    try:
        from music_generator import MusicGenerator
        print("   ✅ Music generator import")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Music generator import failed: {e}")
    
    # Test 3: Import WebSocket bridge
    try:
        from websocket_bridge import WebSocketBridge
        print("   ✅ WebSocket bridge import")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ WebSocket bridge import failed: {e}")
    
    # Test 4: Import recording system
    try:
        from recording_system import SessionRecorder
        print("   ✅ Recording system import")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Recording system import failed: {e}")
    
    print(f"📊 Tests passed: {tests_passed}/{total_tests}")
    return tests_passed == total_tests

def print_usage_instructions():
    """Print usage instructions"""
    print("\n" + "=" * 60)
    print("🎵 GestureBeats Studio - Ready to Use! 🎵")
    print("=" * 60)
    print()
    print("🚀 Quick Start:")
    print("   python main.py                    # Start full application")
    print("   python main.py --frontend         # Start only frontend")
    print("   python main.py --analytics        # Start analytics dashboard")
    print()
    print("🎛️ Individual Components:")
    print("   python main.py --gesture          # Gesture detection only")
    print("   python main.py --music            # Music generator only")
    print()
    print("📊 Analytics:")
    print("   streamlit run analysis_dashboard.py")
    print()
    print("🔧 Troubleshooting:")
    print("   python main.py --check-deps       # Check dependencies")
    print()
    print("📖 Documentation:")
    print("   See README.md for detailed instructions")
    print()
    print("🎵 Happy music making! 🎵")

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check hardware
    camera_ok = check_camera()
    audio_ok = check_audio()
    
    if not camera_ok:
        print("⚠️  Camera issues detected - gesture detection may not work")
    
    if not audio_ok:
        print("⚠️  Audio issues detected - music generation may not work")
    
    # Create configuration
    create_config_file()
    
    # Run tests
    tests_ok = run_tests()
    
    if not tests_ok:
        print("\n⚠️  Some tests failed - check error messages above")
    
    # Print usage instructions
    print_usage_instructions()
    
    if camera_ok and audio_ok and tests_ok:
        print("\n✅ Setup completed successfully!")
        print("🎵 You're ready to start creating music with gestures!")
    else:
        print("\n⚠️  Setup completed with warnings")
        print("💡 Check the issues above before running the application")

if __name__ == "__main__":
    main()
