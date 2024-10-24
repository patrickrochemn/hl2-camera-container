#------------------------------------------------------------------------------
# This script receives microphone audio from the HoloLens, plays it, and
# also publishes the audio data to a NATS topic. The main thread receives the 
# data, decodes it, and puts the decoded audio samples in a queue. A second
# thread gets the samples from the queue, plays them, and publishes them to NATS.
# Audio stream configuration is fixed to 2 channels, 48000 Hz.
# Press esc to stop.
#------------------------------------------------------------------------------

from pynput import keyboard
import hl2ss
import hl2ss_lnm
import hl2ss_utilities
import pyaudio
import queue
import threading
import asyncio
import struct
import json
from nats.aio.client import Client as NATS

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Audio encoding profile
profile = hl2ss.AudioProfile.RAW

# WAV parameters
CHANNELS = 1
SAMPLE_RATE = 16000
BITS_PER_SAMPLE = 16
BYTE_RATE = SAMPLE_RATE * CHANNELS * (BITS_PER_SAMPLE // 8)
BLOCK_ALIGN = CHANNELS * (BITS_PER_SAMPLE // 8)

FORMAT = pyaudio.paInt16
CHUNK = 1024

# NATS settings
NATS_TOPIC = "instructor.1.audio"  # TODO: change topic after dev testing
nats_server = "nats://192.168.9.10:4222"

#------------------------------------------------------------------------------

# Function to generate a basic WAV header
def generate_wav_header(data_size):
    """Generate a WAV file header for the given data size."""
    return struct.pack('<4sI4s4sIHHIIHH4sI',
                       b'RIFF',
                       data_size + 36,  # Chunk size
                       b'WAVE',
                       b'fmt ',
                       16,  # Subchunk1Size for PCM
                       1,   # Audio format (1 is PCM)
                       CHANNELS,
                       SAMPLE_RATE,
                       BYTE_RATE,
                       BLOCK_ALIGN,
                       BITS_PER_SAMPLE,
                       b'data',
                       data_size)  # Subchunk2Size (data size)

async def publish_audio_to_nats(nc, audio_data):
    """Publish audio data as WAV format to the NATS topic."""
    wav_header = generate_wav_header(len(audio_data))
    audio_message = {
        "audio": list(wav_header + audio_data),  # WAV header + audio data
        "stt": "AUDIO STREAMING"  # Optional STT (Speech-to-Text) field
    }

    # Send the audio message
    try:
        dumped = json.dumps(audio_message)
        await nc.publish(NATS_TOPIC, dumped.encode())
    except Exception as e:
        print(f"Error publishing audio to NATS: {e}")

# RAW format is s16 packed, AAC decoded format is f32 planar
audio_format = pyaudio.paInt16 if (profile == hl2ss.AudioProfile.RAW) else pyaudio.paFloat32
enable = True

# Function to handle NATS connection and audio publication
async def nats_publisher():
    """NATS publisher for sending audio data."""
    # Connect to NATS
    nc = NATS()
    print("Connecting to NATS...")
    await nc.connect(nats_server)
    print(f"Connected to NATS server: {nats_server}")

    p = pyaudio.PyAudio()
    stream = p.open(format=audio_format, channels=hl2ss.Parameters_MICROPHONE.CHANNELS, rate=hl2ss.Parameters_MICROPHONE.SAMPLE_RATE, output=True)
    stream.start_stream()

    client = hl2ss_lnm.rx_microphone(host, hl2ss.StreamPort.MICROPHONE, profile=profile)
    client.open()

    while enable:
        data = client.get_next_packet()
        audio = hl2ss_utilities.microphone_planar_to_packed(data.payload) if (profile != hl2ss.AudioProfile.RAW) else data.payload
        audio_bytes = audio.tobytes()
        print(f"Audio bytes: {audio_bytes[:15]}...")

        # Play the audio locally
        stream.write(audio_bytes)

        # Publish the audio to NATS
        await publish_audio_to_nats(nc, audio_bytes)

    # Clean up
    stream.stop_stream()
    stream.close()
    await nc.drain()
    client.close()

# Handle stopping the audio on 'ESC' key press
def on_press(key):
    global enable
    enable = key != keyboard.Key.esc
    return enable

# Start the NATS publisher
def start_async_loop():
    asyncio.run(nats_publisher())

listener = keyboard.Listener(on_press=on_press)
listener.start()

# Run the NATS publisher async task in a separate thread
nats_thread = threading.Thread(target=start_async_loop)
nats_thread.start()

# Wait for keyboard listener to finish
listener.join()
nats_thread.join()
