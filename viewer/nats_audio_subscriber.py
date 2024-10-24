import asyncio
import json
from nats.aio.client import Client as NATS

# NATS settings
NATS_SERVER = "nats://192.168.9.10:4222"  # Replace with your NATS server address
AUDIO_TOPIC = "student.1.audio"  # The audio topic used in the instructor app

async def run():
    nc = NATS()

    # Connect to NATS server
    await nc.connect(NATS_SERVER)

    async def message_handler(msg):
        data = json.loads(msg.data.decode())  # Assuming the data is in JSON format
        print(f"Received message on {msg.subject}: {data}")
        # Print just first 100 bytes of audio data
        print(f"Audio data: {data['audio'][:100]}")
        # print raw first 100 bytes of audio data
        print(f"Audio data raw: {msg.data[:100]}")

    # Subscribe to the topic and bind the handler
    await nc.subscribe(AUDIO_TOPIC, cb=message_handler)

    # Keep the subscriber running
    while True:
        await asyncio.sleep(1)

# Run the subscriber
asyncio.run(run())
