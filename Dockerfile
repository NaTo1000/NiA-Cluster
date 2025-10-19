# Dockerfile - minimal production image for NiA-Cluster
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system deps needed for some Python packages (kept minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy package metadata and source
COPY pyproject.toml setup.py requirements.txt /app/
COPY src/ /app/src/
COPY config/ /app/config/

# Install the package
RUN python -m pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .

# Default configuration file path: /etc/nia-cluster/config.yaml (mount at runtime)
ENTRYPOINT ["nia-cluster"]
CMD ["--help"]
