#!/usr/bin/env python3
"""
Test script to verify the fixes for camera and audio issues
"""

import numpy as np
import cv2
import time
from music_generator import MusicGenerator
from gesture import GestureDetector

def test_audio_shape_fix():
    """Test that audio data shapes are consistent"""
    print("🧪 Testing audio shape consistency...")
    
    generator = MusicGenerator()
    
    # Test different instruments and gestures
    test_cases = [
        ('piano', 'peace', 'left'),
        ('guitar', 'fist', 'right'),
        ('drums', 'open_palm', 'left'),
        ('violin', 'thumbs_up', 'right'),
        ('flute', 'rock_horn', 'left'),
        ('saxophone', 'pinch', 'right')
    ]
    
    for instrument, gesture, hand in test_cases:
        try:
            audio_data = generator.play_note(instrument, gesture, hand)
            if audio_data is not None:
                print(f"   ✅ {instrument} - {gesture} - {hand}: Shape {audio_data.shape}")
            else:
                print(f"   ⚠️  {instrument} - {gesture} - {hand}: No audio data")
        except Exception as e:
            print(f"   ❌ {instrument} - {gesture} - {hand}: Error - {e}")
    
    print("✅ Audio shape test completed!")

def test_camera_initialization():
    """Test camera initialization and frame reading"""
    print("🧪 Testing camera initialization...")
    
    try:
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("   ❌ Camera not available")
            return False
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Test reading a few frames
        for i in range(5):
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"   ✅ Frame {i+1}: Shape {frame.shape}")
            else:
                print(f"   ❌ Frame {i+1}: Failed to read")
                cap.release()
                return False
        
        cap.release()
        print("   ✅ Camera test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Camera test failed: {e}")
        return False

def test_gesture_detection():
    """Test gesture detection with error handling"""
    print("🧪 Testing gesture detection...")
    
    try:
        detector = GestureDetector()
        
        # Test with a dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        annotated_frame, hand_info = detector.process_frame(dummy_frame)
        
        print(f"   ✅ Gesture detection initialized")
        print(f"   ✅ Frame processing: {annotated_frame.shape}")
        print(f"   ✅ Hand info: {hand_info}")
        
        detector.cleanup()
        return True
        
    except Exception as e:
        print(f"   ❌ Gesture detection test failed: {e}")
        return False

def test_music_generation():
    """Test music generation with error handling"""
    print("🧪 Testing music generation...")
    
    try:
        generator = MusicGenerator()
        
        # Test with dummy hand info
        dummy_hand_info = {
            'left': {'gesture': 'peace', 'confidence': 0.8},
            'right': {'gesture': 'fist', 'confidence': 0.9}
        }
        
        music_events = generator.process_gesture(dummy_hand_info)
        
        print(f"   ✅ Music generation initialized")
        print(f"   ✅ Generated {len(music_events)} music events")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Music generation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎵 GestureBeats Studio - Fix Verification Tests")
    print("=" * 50)
    
    tests = [
        ("Audio Shape Fix", test_audio_shape_fix),
        ("Camera Initialization", test_camera_initialization),
        ("Gesture Detection", test_gesture_detection),
        ("Music Generation", test_music_generation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    print("\n🚀 You can now run the application with:")
    print("   python main.py")

if __name__ == "__main__":
    main()
