## Base image:
FROM ubuntu:20.04

LABEL name="raclahe"
LABEL version="3.0"
LABEL mode="api"
LABEL authorization="This Dockerfile is intended to build a container image that will be publicly accessible in the platform images repository."

############## Things done by the root user ##############
USER root

ENV DEBIAN_FRONTEND=noninteractive

# Installation of tools and requirements:
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Create the user (and group) "ds"
RUN groupadd -g 1000 ds && \
    useradd --create-home --shell /bin/bash --uid 1000 --gid 1000 ds

# Default password "password" for ds user
RUN echo "ds:password" | chpasswd

# Copy application files to the container
COPY --chown=ds:ds . /home/ds/

# Install Python requirements
RUN pip install --no-cache-dir -r /home/ds/requirements.txt

############### Now change to normal user ################
USER ds:ds

# Create necessary directories
RUN mkdir -p /home/ds/datasets && \
    mkdir -p /home/ds/persistent-home && \
    mkdir -p /home/ds/persistent-shared-folder && \
    mkdir -p /tmp/raclahe

WORKDIR /home/ds

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI application
ENTRYPOINT ["python3", "/home/ds/api.py"]

