FROM python:3.9-slim

WORKDIR /app

# Install required Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the viewer directory (which includes the webrtc publisher script and HL2SS library)
COPY viewer /app/viewer

# Expose any necessary ports (WebRTC doesn't need port exposure, but it's optional)
EXPOSE 5000

# Set the default command to run the WebRTC publisher
CMD ["python", "/app/viewer/hololens_webrtc_publisher.py"]
