import asyncio
import hl2ss_lnm
import hl2ss
from aiortc import RTCPeerConnection, VideoStreamTrack
import numpy as np

# HoloLens connection settings
HOLOLENS_HOST = "192.168.2.38"  # Update with your HoloLens IP
STREAM_PORT = hl2ss.StreamPort.PERSONAL_VIDEO
WIDTH = 1280
HEIGHT = 720
FRAMERATE = 30  # Default target framerate (can vary)

# WebRTC video track for HoloLens stream
class HoloLensVideoStream(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.frame = None

    def set_frame(self, frame):
        self.frame = frame

    async def recv(self):
        if self.frame is not None:
            return self.frame

async def main_camera_stream(video_stream):
    # Start the HoloLens camera stream
    hl2ss_lnm.start_subsystem_pv(HOLOLENS_HOST, STREAM_PORT, enable_mrc=True, shared=False)

    client = hl2ss_lnm.rx_pv(HOLOLENS_HOST, STREAM_PORT, mode=hl2ss.StreamMode.MODE_0, width=WIDTH, height=HEIGHT, framerate=FRAMERATE, divisor=1, profile=hl2ss.VideoProfile.H264_MAIN, bitrate=None, decoded_format='bgr24')
    client.open()

    while True:
        try:
            data = client.get_next_packet()
            if data.payload and data.payload.image is not None:
                # Directly set the frame without re-encoding
                video_stream.set_frame(data.payload.image)
        except Exception as e:
            print(f"Error while processing frame: {e}")
        await asyncio.sleep(0.03)  # Target ~30 FPS, can adjust based on real frame timing

    client.close()

async def main():
    # Create the WebRTC PeerConnection
    pc = RTCPeerConnection()

    # Create the video stream track from HoloLens
    video_stream = HoloLensVideoStream()
    pc.addTrack(video_stream)

    # Get available video codecs and print them to check capabilities
    codecs = RTCPeerConnection.getCapabilities("video").codecs
    print("Available Codecs: ", codecs)

    # Modify encoding settings without specifying codec
    parameters = pc.getTransceivers()[0].sender.getParameters()
    parameters.encodings[0] = {
        "maxBitrate": 1000000,  # 1 Mbps max bitrate
        "minBitrate": 300000,   # 300 kbps min bitrate for adaptation
        "degradationPreference": "balanced"  # Balance between quality and performance
    }
    await pc.getTransceivers()[0].sender.setParameters(parameters)

    # Start the HoloLens camera stream
    await main_camera_stream(video_stream)

    # Keep the process running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
