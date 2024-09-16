FROM python:3.9-slim

WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the Flask server and static files
COPY webrtc_signaling_server.py /app/
COPY static /app/static

# Expose port for WebRTC signaling and web server
EXPOSE 8080

# Run the Flask signaling server when the container starts
CMD ["python", "/app/webrtc_signaling_server.py"]
