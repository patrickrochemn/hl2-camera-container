import hl2ss_lnm
import hl2ss
import subprocess

# HoloLens connection settings
HOLOLENS_HOST = "192.168.2.38"  # Update with your HoloLens IP
STREAM_PORT = hl2ss.StreamPort.PERSONAL_VIDEO
WIDTH = 1280  # Known width of the HoloLens stream
HEIGHT = 720  # Known height of the HoloLens stream
FRAMERATE = 30

# Start the HoloLens camera stream and send raw H.264 video to FFmpeg for RTSP streaming
def start_hololens_stream():
    # Start subsystem (personal video)
    hl2ss_lnm.start_subsystem_pv(HOLOLENS_HOST, STREAM_PORT, enable_mrc=True, shared=False)

    # Setup the HL2SS client to receive raw H.264 video
    client = hl2ss_lnm.rx_pv(HOLOLENS_HOST, STREAM_PORT, mode=hl2ss.StreamMode.MODE_0,
                             width=WIDTH, height=HEIGHT, framerate=FRAMERATE,
                             divisor=1, profile=hl2ss.VideoProfile.H264_BASE,  # Receive H.264 data
                             bitrate=None, decoded_format=None)  # Do not decode, pass H.264 raw

    client.open()

    # Setup FFmpeg to pass H.264 video directly to RTSP server without re-encoding
    ffmpeg_process = subprocess.Popen([
        'ffmpeg', '-re',
        '-f', 'h264',  # Specify the input format as H.264
        '-fflags', 'nobuffer', # Disable input buffer
        '-flags', 'low_delay', # Enable low-latency mode
        '-i', '-',  # Input from stdin (H.264 stream)
        '-c:v', 'copy',  # No re-encoding
        '-rtsp_transport', 'udp', # Trying UDP for lower latency
        '-f', 'rtsp', 'rtsp://rtsp-server:8554/hololens'  # Output to RTSP server
    ], stdin=subprocess.PIPE)

    # Get raw H.264 frames from HL2SS and send them to FFmpeg
    try:
        while True:
            data = client.get_next_packet()
            if data.payload is not None:
                # Send the raw H.264 frame data to FFmpeg
                ffmpeg_process.stdin.write(data.payload)
    except Exception as e:
        print(f"Error while processing frame: {e}")
    finally:
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()
        client.close()

if __name__ == "__main__":
    start_hololens_stream()
