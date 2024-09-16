import asyncio
from nats.aio.client import Client as NATS
import base64
import cv2
import numpy as np

async def receive_frame(msg):
    # Decode the base64 frame
    frame_data = base64.b64decode(msg.data)
    
    # Convert the JPEG to a NumPy array and then to an OpenCV image
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Display the frame
    cv2.imshow('HoloLens Main Camera Stream', frame)
    cv2.waitKey(1)

async def main():
    # Connect to the NATS server
    nc = NATS()
    await nc.connect("nats://localhost:4222")  # NATS server address
    
    # Subscribe to the NATS subject (topic) where frames are being published
    await nc.subscribe("hololens.maincamera", cb=receive_frame)

    # Run indefinitely to keep receiving frames
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
