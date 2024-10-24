import hl2ss_lnm
import hl2ss_utilities
import hl2ss
import subprocess
import threading

# HoloLens connection settings
HOLOLENS_HOST = "192.168.2.38"
VIDEO_PORT = hl2ss.StreamPort.PERSONAL_VIDEO
WIDTH = 1280
HEIGHT = 720
FRAMERATE = 30
AUDIO_PORT = hl2ss.StreamPort.MICROPHONE

# Audio settings
AUDIO_CHANNELS = hl2ss.Parameters_MICROPHONE.CHANNELS
AUDIO_SAMPLE_RATE = hl2ss.Parameters_MICROPHONE.SAMPLE_RATE
audio_profile = hl2ss.AudioProfile.RAW

def start_video_stream():
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

        # FFmpeg process for video
        ffmpeg_video = subprocess.Popen([
            'ffmpeg', '-re',
            '-f', 'h264',
            '-i', '-',  # Video input from stdin
            '-c:v', 'copy',
            '-f', 'rtsp', 'rtsp://rtsp-server:8554/hololens_video'
        ], stdin=subprocess.PIPE)

        # Send video frames to FFmpeg
        while True:
            data = video_client.get_next_packet()
            if data.payload is not None:
                ffmpeg_video.stdin.write(data.payload)

    except Exception as e:
        print(f"Video stream error: {e}")
    finally:
        video_client.close()

def start_audio_stream():
    try:
        # Setup HL2SS audio client
        audio_client = hl2ss_lnm.rx_microphone(
            HOLOLENS_HOST, AUDIO_PORT, profile=audio_profile
        )
        audio_client.open()

        # FFmpeg process for audio
        ffmpeg_audio = subprocess.Popen([
            'ffmpeg', '-re',
            '-f', 's16le',
            '-ar', str(AUDIO_SAMPLE_RATE),
            '-ac', str(AUDIO_CHANNELS),
            '-i', '-',  # Audio input from stdin
            '-filter:a', 'volume=4.0',
            '-c:a', 'aac',
            '-b:a', '64k',
            '-f', 'rtsp', 'rtsp://rtsp-server:8554/hololens_audio'
        ], stdin=subprocess.PIPE)

        # Send audio frames to FFmpeg
        while True:
            data = audio_client.get_next_packet()
            if data.payload is not None:
                audio_bytes = data.payload.tobytes()
                ffmpeg_audio.stdin.write(audio_bytes)

    except Exception as e:
        print(f"Audio stream error: {e}")
    finally:
        audio_client.close()

if __name__ == "__main__":
    video_thread = threading.Thread(target=start_video_stream)
    audio_thread = threading.Thread(target=start_audio_stream)

    video_thread.start()
    audio_thread.start()

    video_thread.join()
    audio_thread.join()
