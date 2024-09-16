FROM python:3.9-slim

WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the Flask server and static files
COPY nats_flask_server.py /app/
COPY static /app/static

# Expose port 8080 for the web server
EXPOSE 8080

# Run the Flask app when the container starts
CMD ["python", "/app/nats_flask_server.py"]
