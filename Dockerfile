FROM python:3.9-slim

# Set the work directory
WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the Python script that gets the camera stream
COPY viewer /app/viewer

# Expose port if necessary (optional, not required for NATS)
EXPOSE 8080

# Run the Python script when the container starts
CMD ["python", "/app/viewer/client_stream_pv.py"]
