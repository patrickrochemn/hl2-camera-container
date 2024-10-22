import hl2ss_lnm
import hl2ss_utilities
import hl2ss
import subprocess
import threading

# HoloLens connection settings
HOLOLENS_HOST = "192.168.2.38"  # Update with your HoloLens IP
VIDEO_PORT = hl2ss.StreamPort.PERSONAL_VIDEO
WIDTH = 1280  # Known width of the HoloLens stream
HEIGHT = 720  # Known height of the HoloLens stream
FRAMERATE = 30
AUDIO_PORT = hl2ss.StreamPort.MICROPHONE

# Audio settings
AUDIO_CHANNELS = hl2ss.Parameters_MICROPHONE.CHANNELS
AUDIO_SAMPLE_RATE = hl2ss.Parameters_MICROPHONE.SAMPLE_RATE
audio_profile = hl2ss.AudioProfile.AAC_24000

def start_hololens_stream():
    try:
        # Start video subsystem
        hl2ss_lnm.start_subsystem_pv(HOLOLENS_HOST, VIDEO_PORT, enable_mrc=True, shared=False)

        # Setup HL2SS video client
        video_client = hl2ss_lnm.rx_pv(
            HOLOLENS_HOST, VIDEO_PORT, mode=hl2ss.StreamMode.MODE_0,
            width=WIDTH, height=HEIGHT, framerate=FRAMERATE,
            divisor=1, profile=hl2ss.VideoProfile.H264_BASE, bitrate=None, decoded_format=None
        )
        video_client.open()

        # Setup HL2SS audio client
        audio_client = hl2ss_lnm.rx_microphone(
            HOLOLENS_HOST, AUDIO_PORT, profile=audio_profile
        )
        audio_client.open()

        # Setup FFmpeg to handle both video and audio inputs, and output to RTSP
        ffmpeg_process = subprocess.Popen([
            'ffmpeg', '-re',
            '-f', 'h264',  # Video input format
            '-fflags', 'nobuffer',
            '-flags', 'low_delay',
            '-i', '-',  # Video input from stdin
            '-f', 'f32le' if audio_profile != hl2ss.AudioProfile.RAW else 's16le',  # Audio input format
            '-ar', str(AUDIO_SAMPLE_RATE),
            '-ac', str(AUDIO_CHANNELS),
            '-i', '-',  # Audio input from stdin
            '-c:v', 'copy',  # No re-encoding for video
            '-c:a', 'aac',  # Encode audio to AAC for RTSP
            '-rtsp_transport', 'udp',
            '-f', 'rtsp', 'rtsp://rtsp-server:8554/hololens'  # RTSP output URL
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
                        # Convert AAC planar format to packed format if needed
                        audio = hl2ss_utilities.microphone_planar_to_packed(data.payload) if audio_profile != hl2ss.AudioProfile.RAW else data.payload
                        audio_bytes = audio.tobytes()
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

if __name__ == "__main__":
    start_hololens_stream()
