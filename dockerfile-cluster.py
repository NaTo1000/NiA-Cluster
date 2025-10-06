#!/usr/bin/env python3
"""
NiA-Cluster Docker Management Script
Manages Docker containers for the NiA-Cluster system
Internal WiFi/BLE ESP clustering manager with port control and security
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class DockerClusterManager:
    """Manages Docker containers for NiA-Cluster"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "cluster-config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load cluster configuration from JSON file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Return default cluster configuration"""
        return {
            "cluster_name": "nia-cluster",
            "network": {
                "name": "nia-network",
                "driver": "bridge",
                "subnet": "172.20.0.0/16"
            },
            "services": {
                "manager": {
                    "image": "nia-cluster-manager",
                    "ports": ["8080:8080", "1883:1883"],
                    "environment": {
                        "CLUSTER_MODE": "manager",
                        "SECURITY_ENABLED": "true"
                    },
                    "volumes": ["./data:/data", "./config:/config"]
                },
                "esp-controller": {
                    "image": "nia-esp-controller",
                    "ports": ["9000:9000"],
                    "environment": {
                        "ESP_PROTOCOL": "wifi-ble",
                        "PORT_CONTROL": "enabled"
                    }
                }
            }
        }

    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, indent=2, fp=f)
        print(f"Configuration saved to {self.config_path}")

    def generate_dockerfile(self, service: str = "manager") -> str:
        """Generate Dockerfile for specified service"""
        if service == "manager":
            dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    mosquitto-clients \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data /config

# Expose ports for HTTP API and MQTT
EXPOSE 8080 1883

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CLUSTER_MODE=manager

# Run the cluster manager
CMD ["python", "cluster-manager.py"]
"""
        elif service == "esp-controller":
            dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ESP communication
RUN apt-get update && apt-get install -y \\
    bluez \\
    bluetooth \\
    libbluetooth-dev \\
    wireless-tools \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for ESP controller API
EXPOSE 9000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ESP_PROTOCOL=wifi-ble

# Run the ESP controller
CMD ["python", "esp-controller.py"]
"""
        else:
            raise ValueError(f"Unknown service: {service}")

        return dockerfile_content

    def create_dockerfile(self, service: str = "manager", output_path: Optional[str] = None):
        """Create Dockerfile for specified service"""
        content = self.generate_dockerfile(service)
        output_file = output_path or f"Dockerfile.{service}"
        
        with open(output_file, 'w') as f:
            f.write(content)
        
        print(f"Dockerfile created: {output_file}")
        return output_file

    def generate_docker_compose(self) -> str:
        """Generate docker-compose.yml content"""
        compose_content = f"""version: '3.8'

services:
  manager:
    build:
      context: .
      dockerfile: Dockerfile.manager
    container_name: {self.config['cluster_name']}-manager
    ports:
"""
        # Add ports for manager
        for port in self.config['services']['manager']['ports']:
            compose_content += f"      - \"{port}\"\n"
        
        compose_content += "    environment:\n"
        for key, value in self.config['services']['manager']['environment'].items():
            compose_content += f"      - {key}={value}\n"
        
        compose_content += "    volumes:\n"
        for volume in self.config['services']['manager']['volumes']:
            compose_content += f"      - {volume}\n"
        
        compose_content += f"""    networks:
      - {self.config['network']['name']}
    restart: unless-stopped

  esp-controller:
    build:
      context: .
      dockerfile: Dockerfile.esp-controller
    container_name: {self.config['cluster_name']}-esp-controller
    ports:
"""
        # Add ports for esp-controller
        for port in self.config['services']['esp-controller']['ports']:
            compose_content += f"      - \"{port}\"\n"
        
        compose_content += "    environment:\n"
        for key, value in self.config['services']['esp-controller']['environment'].items():
            compose_content += f"      - {key}={value}\n"
        
        compose_content += f"""    privileged: true
    networks:
      - {self.config['network']['name']}
    restart: unless-stopped

networks:
  {self.config['network']['name']}:
    driver: {self.config['network']['driver']}
    ipam:
      config:
        - subnet: {self.config['network']['subnet']}
"""
        return compose_content

    def create_docker_compose(self, output_path: str = "docker-compose.yml"):
        """Create docker-compose.yml file"""
        content = self.generate_docker_compose()
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        print(f"Docker Compose file created: {output_path}")
        return output_path

    def build_images(self, service: Optional[str] = None):
        """Build Docker images"""
        if service:
            cmd = ["docker-compose", "build", service]
            print(f"Building {service} image...")
        else:
            cmd = ["docker-compose", "build"]
            print("Building all images...")
        
        try:
            subprocess.run(cmd, check=True)
            print("Build completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Build failed: {e}")
            sys.exit(1)

    def start_cluster(self):
        """Start the cluster"""
        print("Starting NiA-Cluster...")
        try:
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            print("Cluster started successfully")
            self.status()
        except subprocess.CalledProcessError as e:
            print(f"Failed to start cluster: {e}")
            sys.exit(1)

    def stop_cluster(self):
        """Stop the cluster"""
        print("Stopping NiA-Cluster...")
        try:
            subprocess.run(["docker-compose", "down"], check=True)
            print("Cluster stopped successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to stop cluster: {e}")
            sys.exit(1)

    def status(self):
        """Show cluster status"""
        print("NiA-Cluster Status:")
        try:
            subprocess.run(["docker-compose", "ps"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to get status: {e}")

    def logs(self, service: Optional[str] = None, follow: bool = False):
        """Show logs for services"""
        cmd = ["docker-compose", "logs"]
        if follow:
            cmd.append("-f")
        if service:
            cmd.append(service)
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to get logs: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="NiA-Cluster Docker Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init                    # Initialize cluster configuration
  %(prog)s generate                # Generate all Docker files
  %(prog)s build                   # Build Docker images
  %(prog)s start                   # Start the cluster
  %(prog)s stop                    # Stop the cluster
  %(prog)s status                  # Show cluster status
  %(prog)s logs -f                 # Follow logs
        """
    )

    parser.add_argument(
        'command',
        choices=['init', 'generate', 'build', 'start', 'stop', 'restart', 'status', 'logs'],
        help='Command to execute'
    )
    parser.add_argument(
        '--service',
        choices=['manager', 'esp-controller'],
        help='Specific service to target'
    )
    parser.add_argument(
        '--config',
        default='cluster-config.json',
        help='Path to configuration file (default: cluster-config.json)'
    )
    parser.add_argument(
        '-f', '--follow',
        action='store_true',
        help='Follow log output'
    )

    args = parser.parse_args()

    manager = DockerClusterManager(config_path=args.config)

    if args.command == 'init':
        print("Initializing NiA-Cluster configuration...")
        manager.save_config()
        print("Configuration initialized successfully")

    elif args.command == 'generate':
        print("Generating Docker files...")
        if args.service:
            manager.create_dockerfile(args.service)
        else:
            manager.create_dockerfile('manager')
            manager.create_dockerfile('esp-controller')
            manager.create_docker_compose()
        print("Docker files generated successfully")

    elif args.command == 'build':
        manager.build_images(args.service)

    elif args.command == 'start':
        manager.start_cluster()

    elif args.command == 'stop':
        manager.stop_cluster()

    elif args.command == 'restart':
        manager.stop_cluster()
        manager.start_cluster()

    elif args.command == 'status':
        manager.status()

    elif args.command == 'logs':
        manager.logs(service=args.service, follow=args.follow)


if __name__ == '__main__':
    main()
