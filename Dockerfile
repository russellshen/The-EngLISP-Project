# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files into the container
COPY . /app/

# Accept Private Assets Token as a build argument for private assets injection
ARG PRIVATE_ASSETS_TOKEN

# Conditionally clone private dictionary resources if PRIVATE_ASSETS_TOKEN is supplied
RUN if [ -z "$PRIVATE_ASSETS_TOKEN" ]; then \
        echo "WARNING: PRIVATE_ASSETS_TOKEN build argument is absent. Falling back to public sample dictionary assets."; \
    else \
        echo "PRIVATE_ASSETS_TOKEN detected. Cloned private resources will be integrated."; \
        git clone https://${PRIVATE_ASSETS_TOKEN}@github.com/russellshen/The-EngLISP-Project-Assets.git /tmp/assets && \
        cp /tmp/assets/resources/*.lson /app/englisp/resources/ && \
        rm -rf /tmp/assets; \
    fi

# Expose port 8000 for the FastAPI server
EXPOSE 8000

# Run the application using Gunicorn with Uvicorn workers
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "web.server:app"]

