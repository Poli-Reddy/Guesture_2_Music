#!/usr/bin/env python3
"""
Audio test script for GestureBeats Studio
Tests if audio playback is working correctly
"""

import time
import numpy as np
from music_generator import MusicGenerator

def test_audio_playback():
    """Test basic audio playback"""
    print("🔊 Testing audio playback...")
    
    try:
        generator = MusicGenerator()
        
        # Test different instruments
        test_cases = [
            ('piano', 'peace', 'left'),
            ('guitar', 'fist', 'right'),
            ('drums', 'open_palm', 'left'),
            ('violin', 'thumbs_up', 'right'),
            ('flute', 'rock_horn', 'left'),
            ('saxophone', 'pinch', 'right')
        ]
        
        print("🎵 Playing test notes...")
        
        for i, (instrument, gesture, hand) in enumerate(test_cases):
            print(f"   {i+1}. Playing {instrument} - {gesture} ({hand})")
            
            # Play the note
            audio_data = generator.play_note(instrument, gesture, hand)
            
            if audio_data is not None:
                print(f"      ✅ Audio generated: {audio_data.shape}")
            else:
                print(f"      ❌ No audio generated")
            
            # Wait between notes
            time.sleep(0.5)
        
        print("✅ Audio test completed!")
        
        # Cleanup
        generator.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        return False

def test_simple_tone():
    """Test simple tone generation"""
    print("🎵 Testing simple tone generation...")
    
    try:
        generator = MusicGenerator()
        
        # Generate a simple sine wave
        frequency = 440  # A4 note
        duration = 1.0   # 1 second
        sample_rate = 44100
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(2 * np.pi * frequency * t)
        
        # Convert to stereo
        stereo_tone = np.column_stack([tone, tone])
        
        print("   Playing 440Hz tone for 1 second...")
        
        # Play the tone
        generator._play_audio_data(stereo_tone)
        time.sleep(1.2)  # Wait for playback
        
        print("✅ Simple tone test completed!")
        
        # Cleanup
        generator.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Simple tone test failed: {e}")
        return False

def test_audio_system():
    """Test if audio system is available"""
    print("🔍 Checking audio system...")
    
    try:
        import pyaudio
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Get audio device info
        device_count = p.get_device_count()
        print(f"   Found {device_count} audio devices")
        
        # Check for output devices
        output_devices = []
        for i in range(device_count):
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                output_devices.append(info['name'])
        
        if output_devices:
            print(f"   ✅ Output devices found: {len(output_devices)}")
            for device in output_devices[:3]:  # Show first 3
                print(f"      - {device}")
        else:
            print("   ❌ No output devices found")
            return False
        
        # Test opening a stream
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=2,
            rate=44100,
            output=True
        )
        
        print("   ✅ Audio stream opened successfully")
        
        # Close stream and terminate
        stream.close()
        p.terminate()
        
        return True
        
    except ImportError:
        print("   ❌ PyAudio not installed")
        print("   💡 Install with: pip install pyaudio")
        return False
    except Exception as e:
        print(f"   ❌ Audio system check failed: {e}")
        return False

def main():
    """Run all audio tests"""
    print("🎵 GestureBeats Studio - Audio System Test")
    print("=" * 50)
    
    tests = [
        ("Audio System Check", test_audio_system),
        ("Simple Tone Test", test_simple_tone),
        ("Music Generator Test", test_audio_playback)
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
        print("🎉 All audio tests passed! Music should be audible now.")
    else:
        print("⚠️  Some audio tests failed. Check the error messages above.")
        print("\n💡 Troubleshooting tips:")
        print("   - Check if your speakers/headphones are connected")
        print("   - Check system volume levels")
        print("   - Try running as administrator (Windows)")
        print("   - Check audio device permissions")
    
    print("\n🚀 You can now run the application with:")
    print("   python main.py")

if __name__ == "__main__":
    main()
