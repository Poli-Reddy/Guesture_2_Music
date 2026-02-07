#  GestureBeats Studio 

GestureBeats Studio is a Python-based application that allows you to create music in real-time using hand gestures. It captures your hand movements through a webcam, recognizes predefined gestures, and translates them into musical notes and commands. The application features a web-based interface for easy control and visualization.

##  Features

*   **Real-time Gesture Recognition:** Utilizes Google's MediaPipe library to detect and classify hand gestures from a live camera feed.
*   **Multi-instrument Music Generation:** Supports various instruments for both left and right hands, including piano, guitar, drums, violin, flute, and saxophone.
*   **Interactive Frontend:** A user-friendly web interface built with Streamlit provides controls for instrument selection, volume, tempo, and audio effects.
*   **Recording & Playback:** Record your musical sessions and play them back directly from the application.
*   **Session Analysis:** View statistics and visualizations of your performance, including gesture frequency and complexity.
*   **WebSocket Bridge:** A WebSocket bridge enables communication between the gesture detection backend and the frontend.

##  Setup and Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd gesture-music
```

### 2. Install Dependencies

It is recommended to use a virtual environment.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Audio Setup

For audio playback, you might need to install additional system dependencies. Please refer to the detailed instructions in `AUDIO_SETUP.md`.

A quick test for your audio setup can be run with:
```bash
python test_audio.py
```

##  How to Run

### Accessing the Web Interface (UI)

To access the GestureBeats Studio web interface, follow these steps from your terminal:

1.  **Navigate to the project directory:**
    ```bash
    cd gesture-music
    ```

2.  **Activate your virtual environment:**
    ```bash
    # On Windows
    venv\Scripts\activate

    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Run the main application:**
    ```bash
    python main.py
    ```

4.  **Open the UI in your browser:**
    After running the command, your terminal will display a message similar to this:

    ```
    You can now view your Streamlit app in your browser.

    Local URL: http://localhost:8501
    Network URL: http://<your-local-ip>:8501
    ```

    Open the `Local URL` (`http://localhost:8501`) in your web browser to start using the application.


The application can be launched in different modes using the `main.py` script.

### Full Application

To run the complete application, including the gesture detection backend and the Streamlit frontend, execute:

```bash
python main.py
```

This will start the WebSocket bridge and launch the Streamlit web server. You can access the interface at `http://localhost:8501`.

### Standalone Modes

You can also run individual components of the application:

*   **Frontend only:**
    ```bash
    python main.py --frontend
    ```

*   **Analytics Dashboard:**
    ```bash
    python main.py --analytics
    ```

*   **Gesture Detection (standalone):**
    ```bash
    python main.py --gesture
    ```

*   **Music Generator (test):**
    ```bash
    python main.py --music
    ```

### Check Dependencies

To verify that all required packages are installed correctly, run:
```bash
python main.py --check-deps
```

## Project Structure

```
.
├── frontend.py             # Streamlit frontend application
├── gesture.py              # Hand gesture detection and recognition
├── music_generator.py      # Music generation logic
├── main.py                 # Main application launcher
├── websocket_bridge.py     # WebSocket for backend-frontend communication
├── recording_system.py     # Handles audio recording
├── analysis_dashboard.py   # Streamlit dashboard for session analysis
├── requirements.txt        # Python package dependencies
├── AUDIO_SETUP.md          # Instructions for audio configuration
└── recordings/             # Directory for saved audio and session data
```
