#!/bin/bash

# Start streaming a test video using FFmpeg to the RTSP server
ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=30 -c:v libx264 -f rtsp rtsp://rtsp-server:8554/test
