#!/bin/bash

# Start FFmpeg and stream a test video pattern
ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=30 \
       -vcodec libx264 -tune zerolatency -f rtsp rtsp://rtsp-server:8554/test

