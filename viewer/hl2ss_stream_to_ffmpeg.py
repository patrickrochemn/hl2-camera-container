import hl2ss_lnm
import hl2ss
import subprocess

# HoloLens connection settings
HOLOLENS_HOST = "192.168.2.38"  # Update with your HoloLens IP
STREAM_PORT = hl2ss.StreamPort.PERSONAL_VIDEO
WIDTH = 1280
HEIGHT = 720
FRAMERATE = 30

# Start the HoloLens camera stream and send to FFmpeg
def start_hololens_stream():
    # Start subsystem (personal video)
    hl2ss_lnm.start_subsystem_pv(HOLOLENS_HOST, STREAM_PORT, enable_mrc=True, shared=False)

    # Setup the HL2SS client to receive video
    client = hl2ss_lnm.rx_pv(HOLOLENS_HOST, STREAM_PORT, mode=hl2ss.StreamMode.MODE_0,
                             width=WIDTH, height=HEIGHT, framerate=FRAMERATE,
                             divisor=1, profile=hl2ss.VideoProfile.H264_MAIN,
                             bitrate=None, decoded_format='bgr24')
    client.open()

    # Setup FFmpeg to send video stream to RTSP server
    ffmpeg_process = subprocess.Popen([
        'ffmpeg', '-re', '-f', 'rawvideo', '-pixel_format', 'bgr24', '-video_size', f'{WIDTH}x{HEIGHT}', 
        '-framerate', str(FRAMERATE), '-i', '-', '-c:v', 'libx264', '-f', 'rtsp', 'rtsp://rtsp-server:8554/hololens'
    ], stdin=subprocess.PIPE)

    # Get frames from HL2SS and send them to FFmpeg
    try:
        while True:
            data = client.get_next_packet()
            if data.payload and data.payload.image is not None:
                # Send the raw frame data to FFmpeg
                ffmpeg_process.stdin.write(data.payload.image.tobytes())
    except Exception as e:
        print(f"Error while processing frame: {e}")
    finally:
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()
        client.close()

if __name__ == "__main__":
    start_hololens_stream()
