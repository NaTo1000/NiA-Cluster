FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application code
COPY cluster_manager.py .

# Make the script executable
RUN chmod +x cluster_manager.py

# Set the entrypoint
ENTRYPOINT ["python3", "cluster_manager.py"]

# Default command (can be overridden)
CMD ["--help"]
