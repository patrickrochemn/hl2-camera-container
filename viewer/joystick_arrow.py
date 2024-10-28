import threading
import hl2ss
import hl2ss_lnm
import hl2ss_rus
from scipy.spatial.transform import Rotation as R
import asyncio
import json
from nats.aio.client import Client as NATS

# Settings --------------------------------------------------------------------
host = "192.168.2.38"  # HoloLens address
scale = [5, 5, 5]  # Arrow scale

# Movement increments
move_increment = 0.1  
rotate_increment = 10  # degrees

# Initialize state
enable = True  # Flag to control the hologram thread
pointer_visible = True  # Initial visibility
update_needed = False  # Flag to track updates

# Relative transform deltas
delta_position = [0, 0, 0]
delta_rotation = R.from_quat([0, 0, 0, 1])

# Initial position and rotation
position = [0, 1.2, 1]
# Rotate 90 degrees around the Z-axis to make the arrow point down
initial_rotation = R.from_euler('z', 90, degrees=True).as_quat()
rotation = R.from_quat(initial_rotation)

NATS_TOPIC = "instructor.1.hologram"  # NATS topic for joystick input

def apply_message_data(data):
    """Update position and visibility based on joystick input."""
    global update_needed, pointer_visible, delta_position

    # Toggle visibility
    if 'visible' in data:
        pointer_visible = data['visible']
        print(f"Pointer visibility set to {pointer_visible}")
        update_needed = True

    # Treat joystick inputs as discrete directional controls
    if 'horizontal' in data:
        if data['horizontal'] > 0.9:  # Move right
            delta_position[0] -= move_increment
            update_needed = True
        elif data['horizontal'] < -0.9:  # Move left
            delta_position[0] += move_increment
            update_needed = True

    if 'vertical' in data:
        if data['vertical'] > 0.9:  # Move forward
            delta_position[2] += move_increment
            update_needed = True
        elif data['vertical'] < -0.9:  # Move backward
            delta_position[2] -= move_increment
            update_needed = True

    # New elevation control
    if 'elevation' in data:
        if data['elevation'] > 0.9:  # Move up
            delta_position[1] += move_increment
            update_needed = True
        elif data['elevation'] < -0.9:  # Move down
            delta_position[1] -= move_increment
            update_needed = True

async def nats_subscriber():
    """NATS subscriber to listen for joystick input."""
    nc = NATS()
    await nc.connect("nats://192.168.9.10:4222")

    async def message_handler(msg):
        data = json.loads(msg.data.decode())
        print(f"Received message: {data}")
        apply_message_data(data)  # Apply joystick input

    await nc.subscribe(NATS_TOPIC, cb=message_handler)

    # Keep the subscriber running
    while enable:
        await asyncio.sleep(1)

def hologram_thread():
    """Manipulate the arrow hologram based on joystick input."""
    global update_needed, delta_position, delta_rotation

    ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
    ipc.open()

    # Create the arrow hologram
    display_list = hl2ss_rus.command_buffer()
    display_list.begin_display_list()
    display_list.remove_all()  # Clear existing objects
    display_list.create_arrow()  # Create arrow hologram
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast)  # Use last object
    display_list.set_world_transform(0, position, rotation.as_quat(), scale)
    display_list.set_active(0, hl2ss_rus.ActiveState.Active)
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseID)
    display_list.end_display_list()
    ipc.push(display_list)
    results = ipc.pull(display_list)
    key = results[2]  # Get the arrow's ID

    print(f"Created arrow with ID {key}")

    # Continuously apply updates when needed
    while enable:
        if update_needed:
            display_list = hl2ss_rus.command_buffer()
            display_list.begin_display_list()
            display_list.set_arrow_transform(key, delta_position, delta_rotation.as_quat(), [0, 0, 0])
            if pointer_visible:
                print("Setting active")
                display_list.set_active(key, hl2ss_rus.ActiveState.Active)
            else:
                print("Setting inactive")
                display_list.set_active(key, hl2ss_rus.ActiveState.Inactive)

            display_list.end_display_list()
            ipc.push(display_list)
            results = ipc.pull(display_list)

            # Reset deltas and update flag
            delta_position = [0, 0, 0]
            delta_rotation = R.from_quat([0, 0, 0, 1])
            update_needed = False

    # Cleanup on exit
    display_list = hl2ss_rus.command_buffer()
    display_list.remove(key)
    ipc.push(display_list)
    ipc.close()

# Start the hologram manipulation thread
hologram_thread_instance = threading.Thread(target=hologram_thread)
hologram_thread_instance.start()

# Start the NATS subscriber
asyncio.run(nats_subscriber())
