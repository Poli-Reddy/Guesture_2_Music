# 🔊 Audio Setup Guide for GestureBeats Studio

## Quick Fix for Audio Issues

If you're not hearing music, follow these steps:

### 1. Test Audio System
```bash
python test_audio.py
```

### 2. Install PyAudio (if needed)

**Windows:**
```bash
pip install pyaudio
```

If that fails, try:
```bash
pip install pipwin
pipwin install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### 3. Check System Audio
- Ensure speakers/headphones are connected
- Check system volume levels
- Test with other applications

### 4. Run the Application
```bash
python main.py
```

## Troubleshooting

### No Sound at All
1. **Check Audio Device**: Run `python test_audio.py` to verify audio system
2. **System Volume**: Ensure system volume is up and not muted
3. **Audio Device**: Check if correct audio device is selected in system settings
4. **Permissions**: On some systems, you may need to run as administrator

### Audio Cuts Out or Distorted
1. **Buffer Size**: The audio buffer might be too small
2. **System Resources**: Close other audio applications
3. **Sample Rate**: Try different sample rates in the code

### PyAudio Installation Issues
1. **Windows**: Use `pipwin` instead of `pip`
2. **macOS**: Install portaudio first with homebrew
3. **Linux**: Install development headers first

### Alternative Audio Solutions
If PyAudio doesn't work, you can:
1. Use the web-based audio (Tone.js) - already implemented
2. Save audio to files and play them externally
3. Use a different audio library like `sounddevice`

## Web-Based Audio (Alternative)

The application also includes web-based audio using Tone.js, which works in the browser without requiring PyAudio. This is automatically used in the Streamlit interface.

## Testing Audio

Run these commands to test different aspects:

```bash
# Test basic audio system
python test_audio.py

# Test music generation
python main.py --music

# Test full application
python main.py
```

## Success Indicators

You should see:
- ✅ Audio system initialized successfully
- 🔊 Audio playback started
- Music playing when making gestures
- No error messages about audio

If you see warnings about audio initialization, the web-based audio will still work in the browser interface.
