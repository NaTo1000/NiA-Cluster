FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application code
COPY cluster_manager.py .
COPY dashboard.py .

# Create templates directory for dashboard
RUN mkdir -p templates

# Make the scripts executable
RUN chmod +x cluster_manager.py dashboard.py

# Set the default entrypoint to cluster_manager
ENTRYPOINT ["python3", "cluster_manager.py"]

# Default command (can be overridden)
CMD ["--help"]
