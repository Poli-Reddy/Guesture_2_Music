import asyncio
import websockets
import json
import threading
import time
import queue
from typing import Set, Dict, Any
import logging

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
        
    async def register_client(self, websocket, path):
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
                await self.handle_gesture_data(data)
            elif message_type == 'music_event':
                await self.handle_music_event(data)
            elif message_type == 'control_command':
                await self.handle_control_command(data)
            elif message_type == 'ping':
                await self.send_pong(websocket)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def handle_gesture_data(self, data):
        """Handle gesture detection data"""
        gesture_data = data.get('data', {})
        self.gesture_queue.put(gesture_data)
        
        # Notify all clients about gesture data
        await self.broadcast_to_clients({
            'type': 'gesture_update',
            'data': gesture_data,
            'timestamp': time.time()
        })
        
        # Call registered gesture handlers
        for handler in self.gesture_handlers:
            try:
                handler(gesture_data)
            except Exception as e:
                logger.error(f"Error in gesture handler: {e}")
    
    async def handle_music_event(self, data):
        """Handle music generation events"""
        music_data = data.get('data', {})
        self.music_queue.put(music_data)
        
        # Notify all clients about music events
        await self.broadcast_to_clients({
            'type': 'music_update',
            'data': music_data,
            'timestamp': time.time()
        })
        
        # Call registered music handlers
        for handler in self.music_handlers:
            try:
                handler(music_data)
            except Exception as e:
                logger.error(f"Error in music handler: {e}")
    
    async def handle_control_command(self, data):
        """Handle control commands"""
        control_data = data.get('data', {})
        self.control_queue.put(control_data)
        
        # Notify all clients about control changes
        await self.broadcast_to_clients({
            'type': 'control_update',
            'data': control_data,
            'timestamp': time.time()
        })
        
        # Call registered control handlers
        for handler in self.control_handlers:
            try:
                handler(control_data)
            except Exception as e:
                logger.error(f"Error in control handler: {e}")
    
    async def send_pong(self, websocket):
        """Send pong response to ping"""
        pong_msg = {
            'type': 'pong',
            'timestamp': time.time()
        }
        await websocket.send(json.dumps(pong_msg))
    
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
    
    def get_gesture_data(self, timeout=0.1):
        """Get latest gesture data from queue"""
        try:
            return self.gesture_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_music_data(self, timeout=0.1):
        """Get latest music data from queue"""
        try:
            return self.music_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_control_data(self, timeout=0.1):
        """Get latest control data from queue"""
        try:
            return self.control_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.server = await websockets.serve(
            self.register_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        self.is_running = True
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        
        # Keep server running
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
    
    def get_client_count(self):
        """Get number of connected clients"""
        return len(self.clients)
    
    def get_server_status(self):
        """Get server status information"""
        return {
            'is_running': self.is_running,
            'client_count': len(self.clients),
            'host': self.host,
            'port': self.port,
            'queue_sizes': {
                'gesture': self.gesture_queue.qsize(),
                'music': self.music_queue.qsize(),
                'control': self.control_queue.qsize()
            }
        }

class GestureBeatsBridge:
    """Main bridge class that integrates gesture detection, music generation, and WebSocket communication"""
    
    def __init__(self):
        self.websocket_bridge = WebSocketBridge()
        self.gesture_detector = None
        self.music_generator = None
        self.is_running = False
        
    def initialize_components(self):
        """Initialize gesture detector and music generator"""
        try:
            from gesture import GestureDetector
            from music_generator import MusicGenerator
            
            self.gesture_detector = GestureDetector()
            self.music_generator = MusicGenerator()
            
            # Set up handlers
            self.websocket_bridge.add_gesture_handler(self.handle_gesture_data)
            self.websocket_bridge.add_music_handler(self.handle_music_event)
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
            # Process gesture data with music generator
            if self.music_generator:
                music_events = self.music_generator.process_gesture(gesture_data)
                
                # Send music events to WebSocket clients
                for event in music_events:
                    asyncio.create_task(self.websocket_bridge.broadcast_to_clients({
                        'type': 'music_event',
                        'data': event,
                        'timestamp': time.time()
                    }))
                    
        except Exception as e:
            logger.error(f"Error handling gesture data: {e}")
    
    def handle_music_event(self, music_data):
        """Handle music generation events"""
        try:
            # Process music events
            logger.debug(f"Music event: {music_data}")
            
        except Exception as e:
            logger.error(f"Error handling music event: {e}")
    
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
                    # Broadcast recording result
                    asyncio.create_task(self.websocket_bridge.broadcast_to_clients({
                        'type': 'recording_result',
                        'data': result,
                        'timestamp': time.time()
                    }))
            
            logger.info(f"Control command executed: {command}")
            
        except Exception as e:
            logger.error(f"Error handling control command: {e}")
    
    def start(self):
        """Start the bridge system"""
        if not self.initialize_components():
            return False
        
        # Start WebSocket server
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
    
    def get_status(self):
        """Get system status"""
        return {
            'is_running': self.is_running,
            'websocket_status': self.websocket_bridge.get_server_status(),
            'components': {
                'gesture_detector': self.gesture_detector is not None,
                'music_generator': self.music_generator is not None
            }
        }

# Example usage and testing
if __name__ == "__main__":
    bridge = GestureBeatsBridge()
    
    try:
        if bridge.start():
            print("Bridge started successfully!")
            print(f"Status: {bridge.get_status()}")
            
            # Keep running until interrupted
            while True:
                time.sleep(1)
                
        else:
            print("Failed to start bridge")
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        bridge.stop()
    except Exception as e:
        print(f"Error: {e}")
        bridge.stop()
