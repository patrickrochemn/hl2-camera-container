import asyncio
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

# The topic name to subscribe to (joystick)
JOYSTICK_TOPIC = "instructor.1.hologram"

async def message_handler(msg):
    subject = msg.subject
    data = msg.data.decode()
    print(f"Received a message on topic '{subject}': {data}")

async def subscribe_to_joystick(nc):
    # Subscribe to the joystick topic
    print(f"Subscribing to {JOYSTICK_TOPIC}...")
    await nc.subscribe(JOYSTICK_TOPIC, cb=message_handler)

async def run():
    nc = NATS()

    try:
        # Connect to the NATS server
        await nc.connect("nats://localhost:4222")

        # Subscribe to the joystick topic
        await subscribe_to_joystick(nc)

        # Keep the script running to listen for messages
        while True:
            await asyncio.sleep(1)
    except ErrConnectionClosed:
        print("Connection to NATS closed.")
    except ErrTimeout:
        print("Request timed out.")
    except ErrNoServers:
        print("No NATS servers available.")
    finally:
        if nc.is_connected:
            await nc.drain()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())