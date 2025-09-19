<<<<<<< HEAD
# 🎵 GestureBeats Studio

A revolutionary music creation application that allows you to create music using hand gestures! Control 6 different instruments with 6 unique gestures, record your sessions, and analyze your musical performance with advanced analytics.

## ✨ Features

### 🎹 Instrument System
- **6 Instruments Supported**: Piano, Guitar, Drums, Violin, Flute, Saxophone
- **Dual-Hand Control**: Left and right hands can control different instruments simultaneously
- **Realistic Sound Generation**: High-quality audio synthesis with ADSR envelopes
- **Stereo Separation**: Left/right channel separation for immersive experience

### 👋 Gesture Recognition
- **6 Gestures**: Peace ✌️, Fist ✊, Open Palm ✋, Thumbs Up 👍, Rock Horn 🤘, Pinch 🤏
- **Real-time Detection**: MediaPipe-powered hand tracking with <100ms latency
- **Gesture Smoothing**: Prevents flickering with rolling average filtering
- **Confidence Scoring**: Adjustable sensitivity threshold (0.5-0.9)

### 🎶 Music Tutorials
- **4 Interactive Tutorials**: Piano Basics, Guitar Rhythms, Drum Patterns, String Ensemble
- **Step-by-step Guidance**: Visual indicators show which gestures to make
- **Progressive Learning**: Build skills from basic to advanced techniques

### 💾 Session Recording & Playback
- **Multi-format Recording**: Audio (WAV), Video (MP4), Gesture data (JSON)
- **Synchronized Playback**: Replay sessions with gesture visualization
- **Session Management**: Organize and manage multiple recording sessions

### 📊 Advanced Analytics
- **Performance Metrics**: Gesture frequency, hand usage, tempo analysis
- **Complexity Scoring**: Measure musical sophistication
- **Comparative Analysis**: Compare performance across sessions
- **Visual Insights**: Interactive charts and graphs

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Webcam for gesture detection
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gesturebeats-studio
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run frontend.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:8501`

### Alternative: Run Individual Components

**Gesture Detection Only:**
```bash
python gesture.py
```

**Music Generator Only:**
```bash
python music_generator.py
```

**WebSocket Bridge:**
```bash
python websocket_bridge.py
```

**Analytics Dashboard:**
```bash
streamlit run analysis_dashboard.py
```

## 🎛️ Usage Guide

### Basic Operation

1. **Start the Application**: Run `streamlit run frontend.py`
2. **Enable Camera**: Click "🎬 Start Camera" to begin gesture detection
3. **Select Instruments**: Choose instruments for left and right hands
4. **Make Gestures**: Use the 6 supported gestures to create music
5. **Record Sessions**: Click "🔴 Start Recording" to save your performance

### Gesture Mapping

| Gesture | Piano | Guitar | Drums | Violin | Flute | Saxophone |
|---------|-------|--------|-------|--------|-------|-----------|
| ✌️ Peace | C4 | E2 | Kick | G3 | C5 | Bb3 |
| ✊ Fist | D4 | A2 | Snare | D4 | D5 | C4 |
| ✋ Open Palm | E4 | D3 | Hi-hat | A4 | E5 | D4 |
| 👍 Thumbs Up | F4 | G3 | Crash | E5 | F5 | F4 |
| 🤘 Rock Horn | G4 | B3 | Tom 1 | - | G5 | G4 |
| 🤏 Pinch | A4 | E4 | Tom 2 | - | A5 | A4 |

### Advanced Features

#### Audio Effects
- **Reverb**: Add spatial depth to your sound
- **Delay**: Create echo effects
- **Distortion**: Add grit and character

#### Tempo Control
- Adjust BPM from 60-200
- Real-time tempo changes
- Automatic tempo detection

#### Recording Options
- **Audio Only**: Lightweight WAV recording
- **Video + Audio**: Complete session capture
- **Metadata**: Gesture timeline and instrument mapping

## 📊 Analytics Dashboard

Access comprehensive analytics by running:
```bash
streamlit run analysis_dashboard.py
```

### Available Metrics

- **Performance Overview**: Total sessions, duration, events
- **Gesture Analysis**: Usage frequency and distribution
- **Hand Usage**: Left vs right hand balance
- **Tempo Analysis**: BPM detection and classification
- **Instrument Analysis**: Usage patterns and diversity
- **Comparative Analysis**: Cross-session performance comparison

### Insights & Recommendations

The dashboard provides intelligent insights:
- Gesture diversity assessment
- Hand balance recommendations
- Tempo optimization suggestions
- Complexity scoring and tips

## 🔧 Configuration

### Gesture Sensitivity
Adjust the confidence threshold in the sidebar:
- **Low (0.5)**: More sensitive, may detect false positives
- **Medium (0.7)**: Balanced detection (recommended)
- **High (0.9)**: Less sensitive, requires clear gestures

### Audio Settings
- **Sample Rate**: 44.1 kHz (CD quality)
- **Channels**: Stereo (left/right separation)
- **Bit Depth**: 16-bit

### Video Settings
- **Resolution**: Auto-detected from camera
- **Frame Rate**: 30 FPS
- **Codec**: MP4V for compatibility

## 🐛 Troubleshooting

### Common Issues

**Camera Not Detected:**
- Check camera permissions in browser
- Ensure no other applications are using the camera
- Try refreshing the page

**No Sound:**
- Check browser audio permissions
- Ensure system volume is up
- Try a different browser

**Gesture Detection Issues:**
- Ensure good lighting
- Keep hands visible in frame
- Adjust sensitivity settings
- Try different hand positions

**Performance Issues:**
- Close other applications
- Reduce video quality in settings
- Check system resources

### System Requirements

**Minimum:**
- CPU: Intel i3 or AMD equivalent
- RAM: 4GB
- Camera: 720p webcam
- Browser: Chrome 90+, Firefox 88+, Safari 14+

**Recommended:**
- CPU: Intel i5 or AMD equivalent
- RAM: 8GB
- Camera: 1080p webcam
- Browser: Latest Chrome or Firefox

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black *.py

# Lint code
flake8 *.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **MediaPipe**: Hand detection and tracking
- **Tone.js**: Web audio synthesis
- **Streamlit**: Web application framework
- **OpenCV**: Computer vision processing
- **Plotly**: Data visualization

## 📞 Support

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Check the wiki for detailed guides

## 🎵 Enjoy Creating Music!

GestureBeats Studio is designed to make music creation accessible and fun. Whether you're a beginner exploring music for the first time or an experienced musician looking for new creative tools, we hope you enjoy the experience!

---

*Made with ❤️ for music lovers everywhere*
=======
# Guesture_2_Music
An application designed for music creation through hand gesture recognition.
>>>>>>> 7fc883330bc77a6ce4fe56d1c8158d6643113163
