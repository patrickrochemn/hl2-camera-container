import hl2ss_lnm
import hl2ss
import subprocess

# HoloLens connection settings
HOLOLENS_HOST = "192.168.2.38"  # Update with your HoloLens IP
STREAM_PORT = hl2ss.StreamPort.PERSONAL_VIDEO
WIDTH = 1280  # Known width of the HoloLens stream
HEIGHT = 720  # Known height of the HoloLens stream
FRAMERATE = 30

# Test screen settings
TEST_SCREEN_CMD = [
    'ffmpeg', '-re',
    '-f', 'lavfi', '-i', f'testsrc=size={WIDTH}x{HEIGHT}:rate={FRAMERATE}',
    '-c:v', 'libx264', '-f', 'rtsp', 'rtsp://rtsp-server:8554/hololens'
]

# Start the HoloLens camera stream and send video to FFmpeg
def start_hololens_stream():
    try:
        # Start subsystem (personal video)
        hl2ss_lnm.start_subsystem_pv(HOLOLENS_HOST, STREAM_PORT, enable_mrc=True, shared=False)

        # Setup the HL2SS client to receive video
        client = hl2ss_lnm.rx_pv(HOLOLENS_HOST, STREAM_PORT, mode=hl2ss.StreamMode.MODE_0,
                                 width=WIDTH, height=HEIGHT, framerate=FRAMERATE,
                                 divisor=1, profile=hl2ss.VideoProfile.H264_BASE,
                                 bitrate=None, decoded_format='h264')
        client.open()

        # Setup FFmpeg to send video stream to RTSP server
        ffmpeg_process = subprocess.Popen([
            'ffmpeg', '-re',
            '-f', 'h264', '-i', '-',  # Input from stdin (H.264 stream)
            '-c:v', 'copy',  # Copy the H.264 stream without re-encoding
            '-f', 'rtsp', 'rtsp://rtsp-server:8554/hololens'
        ], stdin=subprocess.PIPE)

        # Get frames from HL2SS and send them to FFmpeg
        try:
            while True:
                data = client.get_next_packet()
                if data.payload and data.payload.image is not None:
                    # Send the raw frame data (H.264) to FFmpeg
                    ffmpeg_process.stdin.write(data.payload.image)
        except Exception as e:
            print(f"Error while processing frame: {e}")
        finally:
            ffmpeg_process.stdin.close()
            ffmpeg_process.wait()
            client.close()

    except Exception as e:
        print(f"Failed to connect to HoloLens: {e}")
        # Run test screen if connection to HoloLens fails
        subprocess.run(TEST_SCREEN_CMD)

if __name__ == "__main__":
    start_hololens_stream()
