import asyncio
import base64
import cv2
import numpy as np
from nats.aio.client import Client as NATS

async def receive_frame(msg):
    # Decode the base64 frame
    frame_data = base64.b64decode(msg.data)
    
    # Convert the JPEG to a NumPy array and then to an OpenCV image
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Display the frame using OpenCV
    if frame is not None:
        cv2.imshow('HoloLens Video Stream', frame)
        cv2.waitKey(1)  # 1ms wait allows frame-by-frame display

async def main():
    # Create NATS client instance
    nc = NATS()

    # Connect to the NATS server
    await nc.connect("nats://localhost:4222")  # Replace with the correct NATS server address

    # Subscribe to the HoloLens video stream subject
    await nc.subscribe("hololens.maincamera", cb=receive_frame)

    # Run indefinitely to keep receiving frames
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    # Start the asyncio loop for NATS
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
