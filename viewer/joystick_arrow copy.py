import threading
import hl2ss
import hl2ss_lnm
import hl2ss_rus
from scipy.spatial.transform import Rotation as R
import asyncio
import json
import time
from nats.aio.client import Client as NATS

# Settings --------------------------------------------------------------------
host = "192.168.2.38"  # HoloLens address
scale = [5, 5, 5]  # Arrow scale (large enough for visibility)
initial_display_time = 3  # Show arrow for 3 seconds at startup

enable = True  # Flag to control the hologram thread
pointer_visible = True  # Initial visibility state
NATS_TOPIC = "instructor.1.hologram"  # NATS topic for joystick data

# Initialize position and rotation
position = [0, 1.6, 1]
rotation = R.from_quat([0, 0, 0, 1])

# Relative transform deltas
delta_position = [0, 0, 0]
delta_rotation = R.from_quat([0, 0, 0, 1])

update_needed = False  # Flag to indicate if an update is needed


def apply_message_data(data):
    """Process joystick data and update position and visibility."""
    global enable, pointer_visible, delta_position, delta_rotation, update_needed

    # Toggle visibility based on the message
    if 'visible' in data:
        pointer_visible = data['visible']

    # Update position based on joystick input
    if 'horizontal' in data:
        delta_position[0] += data['horizontal'] # Left-right movement

    if 'vertical' in data:
        delta_position[2] += data['vertical'] # Forward-backward movement

    # Mark update as needed
    update_needed = True


async def nats_subscriber(ipc, key):
    """NATS subscriber to receive joystick input."""
    nc = NATS()
    await nc.connect("nats://192.168.9.10:4222")

    async def message_handler(msg):
        data = json.loads(msg.data.decode())
        print(f"Received message: {data}")
        apply_message_data(data)  # Apply the message data to the arrow

    # Subscribe to NATS topic
    await nc.subscribe(NATS_TOPIC, cb=message_handler)

    # Keep subscriber alive
    while enable:
        await asyncio.sleep(1)


def update_hologram(ipc, key):
    """Apply transformations and update the hologram's position and visibility."""
    global update_needed

    if update_needed:
        # Create a command buffer and apply the new transform
        display_list = hl2ss_rus.command_buffer()
        display_list.begin_display_list()
        display_list.set_arrow_transform(key, delta_position, delta_rotation.as_quat(), [0,0,0])
        display_list.set_active(key, hl2ss_rus.ActiveState.Active if pointer_visible else hl2ss_rus.ActiveState.Inactive)
        display_list.end_display_list()

        # Push updates to HoloLens
        ipc.push(display_list)
        results = ipc.pull(display_list)  # Ensure the update is applied
        print(f"Updated arrow: Position={position}, Visible={pointer_visible}")

        # Reset the delta values
        delta_position = [0, 0, 0]
        delta_rotation = R.from_quat([0, 0, 0, 1])
        # Reset the update flag
        update_needed = False


def hologram_thread():
    """Create and manipulate the arrow hologram."""
    ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
    ipc.open()

    # Create the arrow hologram
    display_list = hl2ss_rus.command_buffer()
    display_list.begin_display_list()
    display_list.remove_all()  # Clear previous objects
    display_list.create_arrow()  # Create an arrow hologram
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast)  # Use the last created object
    display_list.set_world_transform(0, position, rotation.as_quat(), scale)  # Set initial transform
    display_list.set_active(0, hl2ss_rus.ActiveState.Active)  # Make the arrow visible
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseID)  # Switch back to ID mode
    display_list.end_display_list()

    ipc.push(display_list)
    results = ipc.pull(display_list)
    key = results[2]  # Get the arrow's ID

    print(f"Created arrow with ID {key}")

    # Keep the arrow visible for the initial display time
    time.sleep(initial_display_time)
    print("Initial display time elapsed")

    # Start the NATS subscriber
    asyncio.run(nats_subscriber(ipc, key))

    # Continuously update the hologram when needed
    while enable:
        update_hologram(ipc, key)

    # Cleanup when finished
    display_list = hl2ss_rus.command_buffer()
    display_list.remove(key)
    ipc.push(display_list)
    ipc.close()


# Start the hologram manipulation thread
hologram_thread_instance = threading.Thread(target=hologram_thread)
hologram_thread_instance.start()