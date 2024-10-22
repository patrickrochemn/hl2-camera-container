import threading
import hl2ss
import hl2ss_lnm
import hl2ss_rus
from scipy.spatial.transform import Rotation as R
import asyncio
import json
from nats.aio.client import Client as NATS

# Settings --------------------------------------------------------------------
# HoloLens address
host = "192.168.2.38"

# Initial position in world space (x, y, z) in meters
position = [0, 1.6, 1]

# Initial rotation in world space (x, y, z, w) as a quaternion
rotation = R.from_quat([0, 0, 0, 1])

# Initial scale in meters
scale = [0.2, 0.2, 0.2]

# Initial color
rgba = [0, 1, 0, 1]

# Movement increments
move_increment = 0.1
rotate_increment = 10  # degrees

enable = True
pointer_visible = True

# NATS topic for joystick control
NATS_TOPIC = "instructor.1.hologram"

async def nats_subscriber(position, rotation):
    nc = NATS()
    await nc.connect("nats://192.168.9.10:4222")

    async def message_handler(msg):
        global pointer_visible
        data = json.loads(msg.data.decode())
        print(f"Received a message on topic '{msg.subject}': {data}")

        # Use the data from the NATS message to update position and visibility
        if 'visible' in data:
            pointer_visible = data['visible']
        
        if 'horizontal' in data:
            position[0] += data['horizontal'] * move_increment  # Left-right

        if 'vertical' in data:
            position[2] += data['vertical'] * move_increment  # Forward-backward

    # Subscribe to the NATS topic
    await nc.subscribe(NATS_TOPIC, cb=message_handler)

    # Keep the subscriber running
    while True:
        await asyncio.sleep(1)

# Hologram manipulation thread
def hologram_thread():
    global enable, pointer_visible, position, rotation
    ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
    ipc.open()

    key = 0

    # Create a 3D cube hologram
    display_list = hl2ss_rus.command_buffer()
    display_list.begin_display_list()
    display_list.remove_all()
    display_list.create_primitive(hl2ss_rus.PrimitiveType.Cube)
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast)
    display_list.set_world_transform(key, position, rotation.as_quat(), scale)
    display_list.set_color(key, rgba)
    display_list.set_active(key, hl2ss_rus.ActiveState.Active)
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseID)
    display_list.end_display_list()
    ipc.push(display_list)
    results = ipc.pull(display_list)
    key = results[2]  # Cube ID

    print(f'Created cube with id {key}')

    while enable:
        # Update hologram based on joystick input
        display_list = hl2ss_rus.command_buffer()
        display_list.begin_display_list()
        display_list.set_world_transform(key, position, rotation.as_quat(), scale)
        display_list.set_active(key, hl2ss_rus.ActiveState.Active if pointer_visible else hl2ss_rus.ActiveState.Inactive)
        display_list.end_display_list()
        ipc.push(display_list)
        results = ipc.pull(display_list)

    # Clean up
    command_buffer = hl2ss_rus.command_buffer()
    command_buffer.remove(key)
    ipc.push(command_buffer)
    results = ipc.pull(command_buffer)

    ipc.close()

# Start the hologram manipulation thread
hologram_thread_instance = threading.Thread(target=hologram_thread)
hologram_thread_instance.start()

# Start the NATS subscriber to listen for joystick controls
loop = asyncio.get_event_loop()
loop.run_until_complete(nats_subscriber(position, rotation))
