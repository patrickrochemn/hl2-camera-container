# Use Python as the base image since we need Python and FFmpeg
FROM python:3.9-slim

WORKDIR /app

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the hl2ss directory and viewer files to the container
COPY viewer /app/viewer

# Install Python dependencies (if any)
# You can add a requirements.txt if needed, for now assuming hl2ss dependencies are already resolved
RUN pip install numpy av opencv-python

# Make the Python script executable
RUN chmod +x /app/viewer/hl2ss_stream_to_ffmpeg.py

# Expose the RTSP port (optional)
EXPOSE 8554

# Command to run the HoloLens stream script
CMD ["python", "/app/viewer/hl2ss_stream_to_ffmpeg.py"]
