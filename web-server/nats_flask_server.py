import os
import asyncio
from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from nats.aio.client import Client as NATS

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Serve the index.html page
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# WebSocket connection handler
@socketio.on('connect')
def handle_connect():
    print("Client connected!")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected!")

# NATS subscription function
async def receive_nats_stream():
    nc = NATS()
    await nc.connect(os.getenv('NATS_URL', 'nats://nats-server:4222'))

    async def message_handler(msg):
        # Here we can add code later to send NATS messages to clients
        pass

    # Subscribe to the NATS stream (placeholder for future video stream)
    await nc.subscribe("hololens.maincamera", cb=message_handler)

if __name__ == '__main__':
    # Start NATS subscription in a background thread
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(receive_nats_stream())

    # Start the Flask web server
    socketio.run(app, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
