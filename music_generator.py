import json
import time
import threading
import queue
import numpy as np
import asyncio
import websockets
from collections import deque
import os
import wave
import struct
from datetime import datetime
import pyaudio
import io

class MusicGenerator:
    def __init__(self, sample_rate=44100, channels=2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.recording_data = []
        self.session_metadata = []
        
        # Audio playback
        self.audio_player = None
        self.audio_stream = None
        self.is_audio_playing = False
        self.audio_thread = None
        self.audio_buffer = queue.Queue()
        
        # Initialize audio system
        self._init_audio()
        
        # Instrument definitions with note mappings
        self.instruments = {
            'piano': {
                'name': '🎹 Piano',
                'notes': ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5'],
                'waveform': 'sine',
                'adsr': {'attack': 0.1, 'decay': 0.2, 'sustain': 0.7, 'release': 0.8}
            },
            'guitar': {
                'name': '🎸 Guitar',
                'notes': ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
                'waveform': 'sawtooth',
                'adsr': {'attack': 0.05, 'decay': 0.3, 'sustain': 0.6, 'release': 1.0}
            },
            'drums': {
                'name': '🥁 Drums',
                'notes': ['kick', 'snare', 'hihat', 'crash', 'tom1', 'tom2'],
                'waveform': 'noise',
                'adsr': {'attack': 0.01, 'decay': 0.1, 'sustain': 0.0, 'release': 0.2}
            },
            'violin': {
                'name': '🎻 Violin',
                'notes': ['G3', 'D4', 'A4', 'E5'],
                'waveform': 'sine',
                'adsr': {'attack': 0.2, 'decay': 0.1, 'sustain': 0.8, 'release': 1.5}
            },
            'flute': {
                'name': '🎵 Flute',
                'notes': ['C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5', 'C6'],
                'waveform': 'sine',
                'adsr': {'attack': 0.3, 'decay': 0.1, 'sustain': 0.9, 'release': 0.5}
            },
            'saxophone': {
                'name': '🎷 Saxophone',
                'notes': ['Bb3', 'C4', 'D4', 'F4', 'G4', 'A4', 'Bb4', 'C5'],
                'waveform': 'sawtooth',
                'adsr': {'attack': 0.15, 'decay': 0.2, 'sustain': 0.7, 'release': 1.2}
            }
        }
        
        # Gesture to note mapping
        self.gesture_mapping = {
            'peace': 0,      # First note
            'fist': 1,       # Second note
            'open_palm': 2,  # Third note
            'thumbs_up': 3,  # Fourth note
            'rock_horn': 4,  # Fifth note
            'pinch': 5       # Sixth note
        }
        
        # Current instrument settings
        self.left_instrument = 'piano'
        self.right_instrument = 'guitar'
        self.tempo = 120  # BPM
        self.volume_left = 0.7
        self.volume_right = 0.7
        
        # Audio effects
        self.effects = {
            'reverb': False,
            'delay': False,
            'distortion': False
        }
        
        # WebSocket clients for real-time communication
        self.websocket_clients = set()
    
    def _init_audio(self):
        """Initialize audio system for playback"""
        try:
            self.audio_player = pyaudio.PyAudio()
            self.audio_stream = self.audio_player.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                stream_callback=self._audio_callback
            )
            self.is_audio_playing = True
            print("✅ Audio system initialized successfully")
        except Exception as e:
            print(f"⚠️  Audio initialization failed: {e}")
            print("💡 Audio will be generated but not played through speakers")
            self.audio_player = None
            self.audio_stream = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback for real-time playback"""
        try:
            if not self.audio_buffer.empty():
                audio_data = self.audio_buffer.get_nowait()
                # Ensure we have enough data
                if len(audio_data) >= frame_count * self.channels:
                    return (audio_data[:frame_count * self.channels].tobytes(), pyaudio.paContinue)
                else:
                    # Pad with silence if not enough data
                    padded_data = np.zeros(frame_count * self.channels, dtype=np.float32)
                    padded_data[:len(audio_data)] = audio_data
                    return (padded_data.tobytes(), pyaudio.paContinue)
            else:
                # Return silence if no audio data
                silence = np.zeros(frame_count * self.channels, dtype=np.float32)
                return (silence.tobytes(), pyaudio.paContinue)
        except Exception as e:
            print(f"Audio callback error: {e}")
            silence = np.zeros(frame_count * self.channels, dtype=np.float32)
            return (silence.tobytes(), pyaudio.paContinue)
    
    def _play_audio_data(self, audio_data):
        """Play audio data through speakers"""
        if self.audio_stream and self.is_audio_playing:
            try:
                # Convert to float32 and ensure proper shape
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                
                # Flatten if needed
                if audio_data.ndim > 1:
                    audio_data = audio_data.flatten()
                
                # Add to audio buffer
                self.audio_buffer.put(audio_data)
                
            except Exception as e:
                print(f"Error playing audio: {e}")
    
    def start_audio_playback(self):
        """Start audio playback thread"""
        if self.audio_stream and not self.is_audio_playing:
            self.is_audio_playing = True
            self.audio_stream.start_stream()
            print("🔊 Audio playback started")
    
    def stop_audio_playback(self):
        """Stop audio playback"""
        if self.audio_stream and self.is_audio_playing:
            self.is_audio_playing = False
            self.audio_stream.stop_stream()
            print("🔇 Audio playback stopped")
        
    def note_to_frequency(self, note):
        """Convert note name to frequency"""
        note_freqs = {
            'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
            'G4': 392.00, 'A4': 440.00, 'B4': 493.88, 'C5': 523.25,
            'E2': 82.41, 'A2': 110.00, 'D3': 146.83, 'G3': 196.00,
            'B3': 246.94, 'E4': 329.63, 'G3': 196.00, 'D4': 293.66,
            'A4': 440.00, 'E5': 659.25, 'C5': 523.25, 'D5': 587.33,
            'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00,
            'B5': 987.77, 'C6': 1046.50, 'Bb3': 233.08, 'Bb4': 466.16
        }
        return note_freqs.get(note, 440.0)
    
    def generate_tone(self, frequency, duration, waveform='sine', adsr=None, volume=1.0):
        """Generate a tone with specified parameters"""
        if adsr is None:
            adsr = {'attack': 0.1, 'decay': 0.2, 'sustain': 0.7, 'release': 0.8}
        
        # Use consistent duration to prevent shape issues
        duration = 0.5  # Fixed 0.5 seconds
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples, False)
        
        # Generate base waveform
        if waveform == 'sine':
            wave_data = np.sin(2 * np.pi * frequency * t)
        elif waveform == 'sawtooth':
            wave_data = 2 * (t * frequency - np.floor(t * frequency + 0.5))
        elif waveform == 'square':
            wave_data = np.sign(np.sin(2 * np.pi * frequency * t))
        elif waveform == 'noise':
            wave_data = np.random.normal(0, 0.1, samples)
        else:
            wave_data = np.sin(2 * np.pi * frequency * t)
        
        # Apply ADSR envelope
        envelope = self._apply_adsr(samples, adsr)
        wave_data *= envelope * volume
        
        # Ensure the final audio data is exactly the expected length
        expected_samples = int(0.5 * self.sample_rate)  # 0.5 seconds
        if len(wave_data) != expected_samples:
            if len(wave_data) > expected_samples:
                wave_data = wave_data[:expected_samples]
            else:
                padding = np.zeros(expected_samples - len(wave_data))
                wave_data = np.concatenate([wave_data, padding])
        
        return wave_data
    
    def _apply_adsr(self, samples, adsr):
        """Apply ADSR envelope to audio data"""
        attack_samples = int(adsr['attack'] * self.sample_rate)
        decay_samples = int(adsr['decay'] * self.sample_rate)
        release_samples = int(adsr['release'] * self.sample_rate)
        sustain_samples = samples - attack_samples - decay_samples - release_samples
        
        envelope = np.zeros(samples)
        
        # Attack phase
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay phase
        if decay_samples > 0:
            start_idx = attack_samples
            end_idx = start_idx + decay_samples
            envelope[start_idx:end_idx] = np.linspace(1, adsr['sustain'], decay_samples)
        
        # Sustain phase
        if sustain_samples > 0:
            start_idx = attack_samples + decay_samples
            end_idx = start_idx + sustain_samples
            envelope[start_idx:end_idx] = adsr['sustain']
        
        # Release phase
        if release_samples > 0:
            start_idx = samples - release_samples
            envelope[start_idx:] = np.linspace(adsr['sustain'], 0, release_samples)
        
        return envelope
    
    def generate_drum_sound(self, drum_type, duration=0.5):
        """Generate drum sounds"""
        # Use consistent duration for all drum sounds
        duration = 0.5  # Fixed 0.5 seconds
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples, False)
        
        if drum_type == 'kick':
            # Low frequency thump
            freq = 60
            wave_data = np.sin(2 * np.pi * freq * t) * np.exp(-t * 10)
        elif drum_type == 'snare':
            # High frequency noise burst
            wave_data = np.random.normal(0, 0.3, samples) * np.exp(-t * 15)
        elif drum_type == 'hihat':
            # High frequency noise
            wave_data = np.random.normal(0, 0.1, samples) * np.exp(-t * 20)
        elif drum_type == 'crash':
            # Wide frequency noise
            wave_data = np.random.normal(0, 0.2, samples) * np.exp(-t * 8)
        elif drum_type == 'tom1':
            # Medium frequency
            freq = 150
            wave_data = np.sin(2 * np.pi * freq * t) * np.exp(-t * 5)
        elif drum_type == 'tom2':
            # Higher frequency
            freq = 200
            wave_data = np.sin(2 * np.pi * freq * t) * np.exp(-t * 6)
        else:
            wave_data = np.zeros(samples)
        
        return wave_data
    
    def play_note(self, instrument, gesture, hand='left'):
        """Play a note based on instrument and gesture"""
        try:
            if instrument not in self.instruments:
                return None
            
            inst_config = self.instruments[instrument]
            note_index = self.gesture_mapping.get(gesture, 0)
            
            if note_index >= len(inst_config['notes']):
                note_index = note_index % len(inst_config['notes'])
            
            note = inst_config['notes'][note_index]
            frequency = self.note_to_frequency(note)
            
            # Generate simple sine wave with consistent parameters
            duration = 0.5  # Fixed 0.5 seconds
            samples = int(self.sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            
            # Generate base waveform
            if instrument == 'drums':
                # Simple drum sound
                if note == 'kick':
                    wave_data = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 10)
                elif note == 'snare':
                    wave_data = np.random.normal(0, 0.3, samples) * np.exp(-t * 15)
                elif note == 'hihat':
                    wave_data = np.random.normal(0, 0.1, samples) * np.exp(-t * 20)
                else:
                    wave_data = np.sin(2 * np.pi * 200 * t) * np.exp(-t * 8)
            else:
                # Melodic instruments
                if inst_config['waveform'] == 'sine':
                    wave_data = np.sin(2 * np.pi * frequency * t)
                elif inst_config['waveform'] == 'sawtooth':
                    wave_data = 2 * (t * frequency - np.floor(t * frequency + 0.5))
                elif inst_config['waveform'] == 'square':
                    wave_data = np.sign(np.sin(2 * np.pi * frequency * t))
                else:
                    wave_data = np.sin(2 * np.pi * frequency * t)
            
            # Apply volume
            volume = self.volume_left if hand == 'left' else self.volume_right
            wave_data *= volume
            
            # Apply simple envelope to avoid clicks
            envelope = np.exp(-t * 2)  # Simple exponential decay
            wave_data *= envelope
            
            # Convert to stereo
            if hand == 'left':
                stereo_data = np.column_stack([wave_data, np.zeros_like(wave_data)])
            else:
                stereo_data = np.column_stack([np.zeros_like(wave_data), wave_data])
            
            # Play audio through speakers
            self._play_audio_data(stereo_data)
            
            # Record if recording is active
            if self.is_recording:
                timestamp = time.time()
                self.recording_data.append(stereo_data)
                self.session_metadata.append({
                    'timestamp': timestamp,
                    'instrument': instrument,
                    'gesture': gesture,
                    'hand': hand,
                    'note': note,
                    'duration': duration
                })
            
            return stereo_data
            
        except Exception as e:
            print(f"Error playing note: {e}")
            return None
    
    def _apply_reverb(self, audio_data, room_size=0.3):
        """Apply simple reverb effect"""
        # Simple delay-based reverb
        delay_samples = int(0.1 * self.sample_rate)
        reverb_data = np.zeros_like(audio_data)
        
        for i in range(delay_samples, len(audio_data)):
            reverb_data[i] = audio_data[i] + room_size * reverb_data[i - delay_samples]
        
        return reverb_data
    
    def _apply_delay(self, audio_data, delay_time=0.25, feedback=0.3):
        """Apply delay effect"""
        delay_samples = int(delay_time * self.sample_rate)
        delayed_data = np.zeros_like(audio_data)
        
        for i in range(delay_samples, len(audio_data)):
            delayed_data[i] = audio_data[i] + feedback * delayed_data[i - delay_samples]
        
        return delayed_data
    
    def _apply_distortion(self, audio_data, gain=2.0):
        """Apply distortion effect"""
        # Simple soft clipping distortion
        return np.tanh(audio_data * gain) / gain
    
    def process_gesture(self, hand_info):
        """Process gesture information and generate music"""
        music_events = []
        
        if not hand_info:
            return music_events
        
        for hand, info in hand_info.items():
            try:
                if info and info.get('gesture') and info.get('confidence', 0) > 0.7:
                    instrument = self.left_instrument if hand == 'left' else self.right_instrument
                    audio_data = self.play_note(instrument, info['gesture'], hand)
                    
                    if audio_data is not None:
                        music_events.append({
                            'hand': hand,
                            'instrument': instrument,
                            'gesture': info['gesture'],
                            'audio_data': audio_data,
                            'timestamp': time.time()
                        })
            except Exception as e:
                print(f"Error processing gesture for {hand}: {e}")
                continue
        
        return music_events
    
    def start_recording(self):
        """Start recording session"""
        self.is_recording = True
        self.recording_data = []
        self.session_metadata = []
        print("Recording started...")
    
    def stop_recording(self):
        """Stop recording and save session"""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        
        if not self.recording_data:
            print("No audio data to save")
            return None
        
        # Combine all audio data
        combined_audio = np.concatenate(self.recording_data, axis=0)
        
        # Save audio file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"session_{timestamp}.wav"
        metadata_filename = f"session_{timestamp}.json"
        
        self._save_wav_file(combined_audio, audio_filename)
        self._save_metadata(metadata_filename)
        
        print(f"Session saved: {audio_filename}, {metadata_filename}")
        return audio_filename, metadata_filename
    
    def _save_wav_file(self, audio_data, filename):
        """Save audio data as WAV file"""
        # Normalize audio data
        audio_data = np.clip(audio_data, -1.0, 1.0)
        
        # Convert to 16-bit PCM
        audio_data_16bit = (audio_data * 32767).astype(np.int16)
        
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data_16bit.tobytes())
    
    def _save_metadata(self, filename):
        """Save session metadata as JSON"""
        with open(filename, 'w') as f:
            json.dump(self.session_metadata, f, indent=2)
    
    def load_session(self, audio_filename, metadata_filename):
        """Load a previous session"""
        try:
            with open(metadata_filename, 'r') as f:
                self.session_metadata = json.load(f)
            print(f"Session loaded: {len(self.session_metadata)} events")
            return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False
    
    def get_session_stats(self):
        """Get statistics about the current session"""
        if not self.session_metadata:
            return {}
        
        gesture_counts = {}
        hand_usage = {'left': 0, 'right': 0}
        instrument_usage = {}
        
        for event in self.session_metadata:
            gesture = event['gesture']
            hand = event['hand']
            instrument = event['instrument']
            
            gesture_counts[gesture] = gesture_counts.get(gesture, 0) + 1
            hand_usage[hand] += 1
            instrument_usage[instrument] = instrument_usage.get(instrument, 0) + 1
        
        # Calculate tempo
        if len(self.session_metadata) > 1:
            time_span = self.session_metadata[-1]['timestamp'] - self.session_metadata[0]['timestamp']
            events_per_second = len(self.session_metadata) / time_span
            estimated_bpm = events_per_second * 60
        else:
            estimated_bpm = 0
        
        # Calculate complexity score
        unique_combinations = len(set((e['gesture'], e['instrument']) for e in self.session_metadata))
        complexity_score = unique_combinations / len(self.session_metadata) if self.session_metadata else 0
        
        return {
            'gesture_counts': gesture_counts,
            'hand_usage': hand_usage,
            'instrument_usage': instrument_usage,
            'estimated_bpm': estimated_bpm,
            'complexity_score': complexity_score,
            'total_events': len(self.session_metadata)
        }
    
    def set_instrument(self, hand, instrument):
        """Set instrument for a specific hand"""
        if hand == 'left':
            self.left_instrument = instrument
        else:
            self.right_instrument = instrument
    
    def set_tempo(self, bpm):
        """Set tempo in BPM"""
        self.tempo = max(60, min(200, bpm))
    
    def set_volume(self, hand, volume):
        """Set volume for a specific hand"""
        volume = max(0.0, min(1.0, volume))
        if hand == 'left':
            self.volume_left = volume
        else:
            self.volume_right = volume
    
    def set_effect(self, effect_name, enabled):
        """Enable/disable audio effect"""
        if effect_name in self.effects:
            self.effects[effect_name] = enabled
    
    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections for real-time music streaming"""
        self.websocket_clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.websocket_clients.remove(websocket)
    
    async def broadcast_music_event(self, music_event):
        """Broadcast music event to all connected clients"""
        if self.websocket_clients:
            message = json.dumps({
                'type': 'music_event',
                'data': {
                    'hand': music_event['hand'],
                    'instrument': music_event['instrument'],
                    'gesture': music_event['gesture'],
                    'timestamp': music_event['timestamp']
                }
            })
            
            disconnected = set()
            for client in self.websocket_clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            
            self.websocket_clients -= disconnected
    
    def cleanup(self):
        """Clean up resources"""
        if self.is_recording:
            self.stop_recording()
        
        # Stop and close audio system
        if self.audio_stream:
            self.stop_audio_playback()
            self.audio_stream.close()
        
        if self.audio_player:
            self.audio_player.terminate()

# Example usage
if __name__ == "__main__":
    generator = MusicGenerator()
    
    # Test gesture processing
    test_hand_info = {
        'left': {'gesture': 'peace', 'confidence': 0.8},
        'right': {'gesture': 'fist', 'confidence': 0.9}
    }
    
    music_events = generator.process_gesture(test_hand_info)
    print(f"Generated {len(music_events)} music events")
    
    # Test recording
    generator.start_recording()
    time.sleep(2)
    generator.stop_recording()
    
    # Get stats
    stats = generator.get_session_stats()
    print(f"Session stats: {stats}")
