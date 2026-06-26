#!/bin/bash
# Production runner script for EngLISP Bridge Server using Gunicorn with Uvicorn worker class.
echo "Starting EngLISP Bridge Server in Production Mode..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 web.server:app
