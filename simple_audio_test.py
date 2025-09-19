#!/usr/bin/env python3
"""
Simple audio test to verify the basic audio system works
"""

import numpy as np
import pyaudio
import time

def test_simple_audio():
    """Test simple audio generation and playback"""
    print("🔊 Testing simple audio generation...")
    
    try:
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Audio parameters
        sample_rate = 44100
        duration = 0.5  # 0.5 seconds
        frequency = 440  # A4 note
        
        # Generate a simple sine wave
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        wave_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to stereo
        stereo_data = np.column_stack([wave_data, wave_data])
        
        # Open audio stream
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=2,
            rate=sample_rate,
            output=True
        )
        
        print(f"   Playing {frequency}Hz tone for {duration} seconds...")
        print(f"   Audio shape: {stereo_data.shape}")
        
        # Play the audio
        stream.write(stereo_data.astype(np.float32).tobytes())
        
        # Close stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("✅ Simple audio test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Simple audio test failed: {e}")
        return False

def test_multiple_notes():
    """Test playing multiple notes in sequence"""
    print("🎵 Testing multiple notes...")
    
    try:
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Audio parameters
        sample_rate = 44100
        duration = 0.3  # 0.3 seconds per note
        frequencies = [261.63, 293.66, 329.63, 349.23, 392.00]  # C, D, E, F, G
        
        # Open audio stream
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=2,
            rate=sample_rate,
            output=True
        )
        
        for i, freq in enumerate(frequencies):
            print(f"   Playing note {i+1}: {freq}Hz")
            
            # Generate sine wave
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            wave_data = np.sin(2 * np.pi * freq * t)
            
            # Convert to stereo
            stereo_data = np.column_stack([wave_data, wave_data])
            
            # Play the audio
            stream.write(stereo_data.astype(np.float32).tobytes())
            
            # Small pause between notes
            time.sleep(0.1)
        
        # Close stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("✅ Multiple notes test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Multiple notes test failed: {e}")
        return False

def main():
    """Run simple audio tests"""
    print("🎵 Simple Audio Test for GestureBeats Studio")
    print("=" * 50)
    
    tests = [
        ("Simple Audio", test_simple_audio),
        ("Multiple Notes", test_multiple_notes)
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
        print("🎉 Basic audio system is working!")
        print("💡 The issue might be in the complex audio generation code.")
    else:
        print("⚠️  Basic audio system has issues.")
        print("💡 Check your audio setup and PyAudio installation.")

if __name__ == "__main__":
    main()
