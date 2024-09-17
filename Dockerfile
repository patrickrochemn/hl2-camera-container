# Use Debian Slim for a lightweight base
FROM debian:bullseye-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the script that will run the FFmpeg stream
COPY start_stream.sh /app/start_stream.sh
RUN chmod +x /app/start_stream.sh

# Expose the RTSP port
EXPOSE 8554
