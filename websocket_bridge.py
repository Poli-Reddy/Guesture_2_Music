import asyncio
import websockets
import json
import threading
import time
import queue
from typing import Set, Dict, Any
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketBridge:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.is_running = False
        
        # Message queues for different data types
        self.gesture_queue = queue.Queue()
        self.music_queue = queue.Queue()
        self.control_queue = queue.Queue()
        
        # Event handlers
        self.gesture_handlers = []
        self.music_handlers = []
        self.control_handlers = []
        
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        client_address = websocket.remote_address
        logger.info(f"Client connected: {client_address}")
        
        try:
            # Send welcome message
            welcome_msg = {
                'type': 'connection',
                'status': 'connected',
                'timestamp': time.time(),
                'message': 'Welcome to GestureBeats Studio!'
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Keep connection alive and handle messages
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_address}")
        except Exception as e:
            logger.error(f"Error handling client {client_address}: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_message(self, websocket, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            if message_type == 'gesture_data':
                for handler in self.gesture_handlers:
                    handler(data.get('data', {}))
            elif message_type == 'control_command':
                for handler in self.control_handlers:
                    handler(data.get('data', {}))
            elif message_type == 'ping':
                await self.send_pong(websocket)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def broadcast_to_clients(self, message: Dict[Any, Any]):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
        
        message_str = json.dumps(message)
        disconnected_clients = set()
        
        for client in self.clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    def add_gesture_handler(self, handler):
        """Add a gesture data handler"""
        self.gesture_handlers.append(handler)
    
    def add_music_handler(self, handler):
        """Add a music event handler"""
        self.music_handlers.append(handler)
    
    def add_control_handler(self, handler):
        """Add a control command handler"""
        self.control_handlers.append(handler)
    
    async def start_server(self):
        """Start the WebSocket server"""
        async def handler(websocket):
            await self.register_client(websocket)

        self.server = await websockets.serve(
            handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        self.is_running = True
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        
        await self.server.wait_closed()
    
    def start_server_thread(self):
        """Start WebSocket server in a separate thread"""
        def run_server():
            asyncio.run(self.start_server())
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        return server_thread
    
    def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            self.is_running = False
            logger.info("WebSocket server stopped")

class GestureBeatsBridge:
    """Main bridge class that integrates gesture detection, music generation, and WebSocket communication"""
    
    def __init__(self):
        self.websocket_bridge = WebSocketBridge()
        self.music_generator = None
        self.is_running = False
        
    def initialize_components(self):
        """Initialize music generator"""
        try:
            from music_generator import MusicGenerator
            self.music_generator = MusicGenerator()
            self.websocket_bridge.add_gesture_handler(self.handle_gesture_data)
            self.websocket_bridge.add_control_handler(self.handle_control_command)
            logger.info("Components initialized successfully")
            return True
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False

    def handle_gesture_data(self, gesture_data):
        """Handle incoming gesture data"""
        try:
            if self.music_generator:
                self.music_generator.process_gesture(gesture_data)
        except Exception as e:
            logger.error(f"Error handling gesture data: {e}")
    
    def handle_control_command(self, control_data):
        """Handle control commands"""
        try:
            command = control_data.get('command')
            params = control_data.get('params', {})
            
            if command == 'set_instrument':
                hand = params.get('hand')
                instrument = params.get('instrument')
                if self.music_generator and hand and instrument:
                    self.music_generator.set_instrument(hand, instrument)
                    
            elif command == 'set_tempo':
                tempo = params.get('tempo')
                if self.music_generator and tempo:
                    self.music_generator.set_tempo(tempo)
                    
            elif command == 'set_volume':
                hand = params.get('hand')
                volume = params.get('volume')
                if self.music_generator and hand and volume is not None:
                    self.music_generator.set_volume(hand, volume)
                    
            elif command == 'set_effect':
                effect = params.get('effect')
                enabled = params.get('enabled')
                if self.music_generator and effect is not None and enabled is not None:
                    self.music_generator.set_effect(effect, enabled)
                    
            elif command == 'start_recording':
                if self.music_generator:
                    self.music_generator.start_recording()
                    
            elif command == 'stop_recording':
                if self.music_generator:
                    result = self.music_generator.stop_recording()
                    if result:
                        audio_filename, _ = result
                        stats = self.music_generator.get_session_stats()
                        stats_filename = audio_filename.replace('.wav', '_stats.json')
                        with open(stats_filename, 'w') as f:
                            json.dump(stats, f, indent=2)
            
            logger.info(f"Control command executed: {command}")
            
        except Exception as e:
            logger.error(f"Error handling control command: {e}")
    
    def start(self):
        """Start the bridge system"""
        if not self.initialize_components():
            return False
        
        self.websocket_bridge.start_server_thread()
        self.is_running = True
        
        logger.info("GestureBeats Bridge started successfully")
        return True
    
    def stop(self):
        """Stop the bridge system"""
        self.is_running = False
        self.websocket_bridge.stop_server()
        
        if self.music_generator:
            self.music_generator.cleanup()
        
        logger.info("GestureBeats Bridge stopped")

if __name__ == "__main__":
    bridge = GestureBeatsBridge()
    
    try:
        if bridge.start():
            print("Bridge started successfully!")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        bridge.stop()
    except Exception as e:
        print(f"Error: {e}")
        bridge.stop()