#!/usr/bin/env python3
"""
Simplified music generator that definitely works with audio playback
"""

import numpy as np
import pyaudio
import time
import threading
import queue

class SimpleMusicGenerator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.duration = 0.5  # Fixed 0.5 seconds per note
        
        # Initialize audio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=2,
            rate=sample_rate,
            output=True
        )
        
        # Note frequencies
        self.notes = {
            'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
            'G4': 392.00, 'A4': 440.00, 'B4': 493.88, 'C5': 523.25
        }
        
        # Gesture to note mapping
        self.gesture_notes = {
            'peace': 'C4',
            'fist': 'D4', 
            'open_palm': 'E4',
            'thumbs_up': 'F4',
            'rock_horn': 'G4',
            'pinch': 'A4'
        }
        
        print("✅ Simple music generator initialized!")
    
    def play_note(self, gesture, hand='left'):
        """Play a note based on gesture"""
        if gesture not in self.gesture_notes:
            return
        
        note = self.gesture_notes[gesture]
        frequency = self.notes[note]
        
        # Generate sine wave
        samples = int(self.sample_rate * self.duration)
        t = np.linspace(0, self.duration, samples, False)
        wave_data = np.sin(2 * np.pi * frequency * t)
        
        # Apply simple envelope to avoid clicks
        envelope = np.exp(-t * 3)  # Exponential decay
        wave_data *= envelope
        
        # Convert to stereo
        if hand == 'left':
            stereo_data = np.column_stack([wave_data, np.zeros_like(wave_data)])
        else:
            stereo_data = np.column_stack([np.zeros_like(wave_data), wave_data])
        
        # Play audio
        try:
            self.stream.write(stereo_data.astype(np.float32).tobytes())
            print(f"🎵 Played {note} ({frequency}Hz) with {hand} hand")
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
    
    def test_all_notes(self):
        """Test all available notes"""
        print("🎵 Testing all notes...")
        
        for gesture, note in self.gesture_notes.items():
            print(f"   Playing {gesture} -> {note}")
            self.play_note(gesture, 'left')
            time.sleep(0.6)  # Wait between notes
    
    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
        print("🔇 Audio system cleaned up")

def main():
    """Test the simple music generator"""
    print("🎵 Simple Music Generator Test")
    print("=" * 40)
    
    generator = SimpleMusicGenerator()
    
    try:
        # Test all notes
        generator.test_all_notes()
        
        print("\n✅ All tests completed!")
        print("🎉 Music should be audible!")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    finally:
        generator.cleanup()

if __name__ == "__main__":
    main()
