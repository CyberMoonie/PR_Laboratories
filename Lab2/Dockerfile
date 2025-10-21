# Use Python 3.11 slim as base image
# This is a lightweight Linux distribution with Python pre-installed
FROM python:3.11-slim

# Set working directory inside the container
# All commands will run from this directory
WORKDIR /app

# Copy Python files into the container
# This includes our server and client scripts
COPY lab2.py /app/
COPY client.py /app/

# Copy content directory into the container 
# This includes all files that the server will serve
COPY content/ /app/content/

# Create downloads directory for any client downloads
RUN mkdir -p /app/downloads

# Expose port 8000 to allow external connections
# This tells Docker to allow connections on port 8000
EXPOSE 8000

# Create non-root user for security
# Running as root inside containers is bad practice
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Default command when container starts
# This starts our multithreaded HTTP server
CMD ["python3", "lab2.py", "content"]