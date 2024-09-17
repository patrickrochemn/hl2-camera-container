import hl2ss_lnm
import hl2ss
import subprocess

# HoloLens connection settings
HOLOLENS_HOST = "192.168.2.38"  # Update with your HoloLens IP
STREAM_PORT = hl2ss.StreamPort.PERSONAL_VIDEO
WIDTH = 1280
HEIGHT = 720
FRAMERATE = 30

# Start the HoloLens camera stream
def start_hololens_stream():
    hl2ss_lnm.start_subsystem_pv(HOLOLENS_HOST, STREAM_PORT, enable_mrc=True, shared=False)

    client = hl2ss_lnm.rx_pv(HOLOLENS_HOST, STREAM_PORT, mode=hl2ss.StreamMode.MODE_0, width=WIDTH, height=HEIGHT, framerate=FRAMERATE, divisor=1, profile=hl2ss.VideoProfile.H264_MAIN, bitrate=None, decoded_format='bgr24')
    client.open()

    # Loop to get frames from the HoloLens
    while True:
        try:
            data = client.get_next_packet()
            if data.payload and data.payload.image is not None:
                # Send the frame to FFmpeg or GStreamer
                frame = data.payload.image
                # Use FFmpeg or GStreamer to stream this frame over RTSP
                ffmpeg_process.stdin.write(frame.tobytes())
        except Exception as e:
            print(f"Error while processing frame: {e}")

    client.close()

# Start FFmpeg process for RTSP streaming
def start_ffmpeg():
    return subprocess.Popen([
        'ffmpeg', 
        '-f', 'rawvideo', 
        '-pixel_format', 'bgr24', 
        '-video_size', f'{WIDTH}x{HEIGHT}', 
        '-framerate', str(FRAMERATE),
        '-i', '-',  # Input from stdin
        '-c:v', 'libx264',  # Codec
        '-f', 'rtsp', 
        'rtsp://0.0.0.0:8554/hololens'  # RTSP output
    ], stdin=subprocess.PIPE)

if __name__ == "__main__":
    # Start the FFmpeg process
    ffmpeg_process = start_ffmpeg()

    # Start fetching the video from HoloLens and piping it to FFmpeg
    start_hololens_stream()
