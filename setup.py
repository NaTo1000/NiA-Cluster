#!/usr/bin/env python3
"""Setup script for NiA-Cluster"""
from setuptools import setup, find_packages

setup(
    name="nia-cluster",
    version="1.0.0",
    description="Internal WiFi/BLE ESP clustering manager with port control and security",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "websockets>=12.0",
    ],
    entry_points={
        "console_scripts": [
            "nia-cluster=nia_cluster.cluster_manager:main",
        ],
    },
)
