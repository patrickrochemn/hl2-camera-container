import os
import cv2
import hl2ss_lnm
import hl2ss
import threading
from nats.aio.client import Client as NATS
import asyncio
import base64

# Fetch the HoloLens host address from environment variables
# Default to '192.168.9.38' if not set
host = os.getenv('HOLOLENS_HOST', '192.168.9.38')
print(f"Connecting to HoloLens at {host}")

# Settings --------------------------------------------------------------------
mode = hl2ss.StreamMode.MODE_0
enable_mrc = True
shared = False
width = 1920
height = 1080
framerate = 30
divisor = 1
profile = hl2ss.VideoProfile.H264_MAIN
bitrate = None
decoded_format = 'bgr24'

running = True

async def publish_to_nats(nc, subject, message):
    await nc.publish(subject, message)

async def main_camera_stream():
    # Connect to NATS
    nc = NATS()
    await nc.connect("nats://nats-server:4222")  # Use your NATS server address here

    # Start PV subsystem on HoloLens
    hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, enable_mrc=enable_mrc, shared=shared)

    client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=mode, width=width, height=height, framerate=framerate, divisor=divisor, profile=profile, bitrate=bitrate, decoded_format=decoded_format)
    client.open()

    while running:
        data = client.get_next_packet()
        if data.payload and data.payload.image is not None:
            # Convert frame to JPEG
            ret, jpeg = cv2.imencode('.jpg', data.payload.image)
            if ret:
                # Encode the JPEG frame as base64
                encoded_frame = base64.b64encode(jpeg).decode('utf-8')

                # Publish the encoded frame to the NATS subject (topic)
                await publish_to_nats(nc, "hololens.maincamera", encoded_frame.encode('utf-8'))
            else:
                print("Failed to encode image to JPEG")

    client.close()
    await nc.close()

if __name__ == '__main__':
    # Use asyncio to handle the NATS publish loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_camera_stream())
