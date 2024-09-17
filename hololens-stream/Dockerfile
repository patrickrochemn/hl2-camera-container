FROM python:3.9-slim

# Install necessary libraries
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean

# Set up working directory
WORKDIR /app

# Copy the HL2SS Python script and required files
COPY viewer /app/viewer

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Expose RTSP port (default is 8554)
EXPOSE 8554

# Set environment variables
ENV HOLOLENS_HOST=192.168.2.38

# Run the RTSP streaming script
CMD ["python", "/app/viewer/hololens_rtsp_stream.py"]
