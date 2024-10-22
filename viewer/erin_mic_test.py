import pyaudio
import asyncio
import wave
import struct
import json
from nats.aio.client import Client as NATS

# WAV file parameters
CHANNELS = 1
SAMPLE_RATE = 16000
BITS_PER_SAMPLE = 16
BYTE_RATE = SAMPLE_RATE * CHANNELS * (BITS_PER_SAMPLE // 8)
BLOCK_ALIGN = CHANNELS * (BITS_PER_SAMPLE // 8)

FORMAT = pyaudio.paInt16
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "eeg.wav"

NATS_TOPIC = "instructor.1.audio"  # NATS topic for audio
nats_server = "nats://127.0.0.1:4222"  # NATS server address
frames = []
audio = pyaudio.PyAudio()


# Function to generate a basic WAV header
def generate_wav_header(data):
    data_size = len(data)
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

# Function to publish audio data to NATS
async def publish_audio_to_nats(nc, audio_data):
    """Publish audio data as WAV format to the NATS topic."""
    wav_header = generate_wav_header(audio_data)
    audio_message = {
        "audio": list(wav_header + audio_data),  # WAV header + audio dat# WAV header + audio data
        "stt": "AUDIO STREAMING"  # Optional STT (Speech-to-Text) field
    }

    # Send the audio message
    dumped = json.dumps(audio_message)
    print (dumped.encode())
    await nc.publish(NATS_TOPIC, dumped.encode())
    #await nc.publish(NATS_TOPIC, json.loads(audio_message).encode())

# Function to handle NATS connection and audio publication
async def nats_publisher(audio_bytes):
    """NATS publisher for sending audio data."""
    # Connect to NATS
    nc = NATS()
    print("Connecting to NATS...")
    await nc.connect(nats_server)
    print(f"Connected to NATS server: {nats_server}")

    """
    # Initialize client to receive audio from HoloLens
    client = hl2ss_lnm.rx_microphone(host, hl2ss.StreamPort.MICROPHONE, profile=profile)
    client.open()

    while enable:
        # Receive the next audio packet
        data = client.get_next_packet()
        print(f"Received {len(data.payload)} bytes")

        # Convert the audio to packed format (RAW is s16 packed, AAC is f32 planar)
        audio = hl2ss_utilities.microphone_planar_to_packed(data.payload) if profile != hl2ss.AudioProfile.RAW else data.payload
        audio_bytes = audio.tobytes()

        # Publish the audio bytes as a WAV-formatted message
        await publish_audio_to_nats(nc, audio_bytes)
    """


    await publish_audio_to_nats(nc, audio_bytes)
    # Close the NATS connection
    await nc.drain()
    #client.close()



def get_audio() -> bytes:
    # start Recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=SAMPLE_RATE, input=True,
                    frames_per_buffer=CHUNK)
    print ("recording...")
    frames = []
    audio_bytes = bytearray()
    for i in range(0, int(SAMPLE_RATE/ CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        audio_bytes.extend(data)
    print ("finished recording")
    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    saveWav(frames)
    return audio_bytes


def saveWav(frames):
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(SAMPLE_RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()


# Run the NATS publisher async tas
audio_data = get_audio()
asyncio.run(nats_publisher(audio_data))