import hl2ss_lnm
import hl2ss
import subprocess
import time
import threading

# HoloLens connection settings
HOLOLENS_HOST = "192.168.2.38"  # Update with your HoloLens IP
VIDEO_STREAM_PORT = hl2ss.StreamPort.PERSONAL_VIDEO
AUDIO_STREAM_PORT = hl2ss.StreamPort.MICROPHONE

# Video settings
WIDTH = 1280  # Known width of the HoloLens stream
HEIGHT = 720  # Known height of the HoloLens stream
FRAMERATE = 30
TEST_DURATION = 30  # Duration in seconds to show the test screen if HoloLens is unavailable

# Audio settings
AUDIO_CHANNELS = hl2ss.Parameters_MICROPHONE.CHANNELS
AUDIO_SAMPLE_RATE = hl2ss.Parameters_MICROPHONE.SAMPLE_RATE

# Start the HoloLens video stream and audio stream, send to FFmpeg for RTSP
def start_hololens_stream():
    try:
        # Start subsystems (personal video and microphone)
        hl2ss_lnm.start_subsystem_pv(HOLOLENS_HOST, VIDEO_STREAM_PORT, enable_mrc=True, shared=False)
        hl2ss_lnm.start_subsystem_microphone(HOLOLENS_HOST, AUDIO_STREAM_PORT)

        # Setup HL2SS video client to receive raw H.264 video
        video_client = hl2ss_lnm.rx_pv(
            HOLOLENS_HOST, VIDEO_STREAM_PORT, mode=hl2ss.StreamMode.MODE_0,
            width=WIDTH, height=HEIGHT, framerate=FRAMERATE,
            divisor=1, profile=hl2ss.VideoProfile.H264_BASE, bitrate=None, decoded_format=None
        )
        video_client.open()

        # Setup HL2SS audio client to receive microphone audio
        audio_client = hl2ss_lnm.rx_microphone(HOLOLENS_HOST, AUDIO_STREAM_PORT, profile=hl2ss.AudioProfile.RAW)
        audio_client.open()

        # Setup FFmpeg to handle video and audio inputs, and output to RTSP
        ffmpeg_process = subprocess.Popen([
            'ffmpeg', '-re',
            '-f', 'h264',  # Video input format
            '-fflags', 'nobuffer',
            '-flags', 'low_delay',
            '-i', '-',  # Video input from stdin
            '-f', 's16le',  # Audio input format (16-bit PCM)
            '-ar', str(AUDIO_SAMPLE_RATE),
            '-ac', str(AUDIO_CHANNELS),
            '-i', '-',  # Audio input from stdin
            '-c:v', 'copy',  # No re-encoding for video
            '-c:a', 'aac',  # Encode audio to AAC for RTSP
            '-rtsp_transport', 'udp',
            '-f', 'rtsp', 'rtsp://192.168.9.10:8554/hololens'  # RTSP output URL
        ], stdin=subprocess.PIPE)

        def stream_video():
            try:
                while True:
                    data = video_client.get_next_packet()
                    if data.payload is not None:
                        ffmpeg_process.stdin.write(data.payload)
            except Exception as e:
                print(f"Video stream error: {e}")
            finally:
                video_client.close()

        def stream_audio():
            try:
                while True:
                    data = audio_client.get_next_packet()
                    if data.payload is not None:
                        audio_bytes = data.payload.tobytes()
                        ffmpeg_process.stdin.write(audio_bytes)
            except Exception as e:
                print(f"Audio stream error: {e}")
            finally:
                audio_client.close()

        # Start separate threads for video and audio streaming
        video_thread = threading.Thread(target=stream_video)
        audio_thread = threading.Thread(target=stream_audio)

        video_thread.start()
        audio_thread.start()

        video_thread.join()
        audio_thread.join()

        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()

    except Exception as e:
        print(f"HoloLens connection failed: {e}")
        print("Showing test screen...")
        show_test_screen()

def show_test_screen():
    ffmpeg_process = subprocess.Popen([
        'ffmpeg', '-re', '-f', 'lavfi', '-i', f'testsrc=size={WIDTH}x{HEIGHT}:rate={FRAMERATE}',
        '-c:v', 'libx264', '-preset', 'ultrafast',
        '-f', 'rtsp', 'rtsp://rtsp-server:8554/hololens'
    ])

    try:
        time.sleep(TEST_DURATION)
    except KeyboardInterrupt:
        pass
    finally:
        ffmpeg_process.terminate()

if __name__ == "__main__":
    start_hololens_stream()
