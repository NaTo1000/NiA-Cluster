# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for GUI and networking tools
RUN apt-get update && apt-get install -y \
    python3-tk \
    tk-dev \
    python3-dev \
    build-essential \
    net-tools \
    iputils-ping \
    wireless-tools \
    bluez \
    bluetooth \
    libbluetooth-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY cluster_gui_suite.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0

# Expose ports for cluster communication
EXPOSE 8080 8443 5000

# Run the application
CMD ["python", "cluster_gui_suite.py"]
