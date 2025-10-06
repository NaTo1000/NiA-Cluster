#!/usr/bin/env python3
"""
NiA-Cluster Setup Configuration
Advanced networking cluster tool with AI integration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nia-cluster",
    version="0.1.0",
    author="NaTo1000",
    description="Internal wifi ble esp clustering manager with portcontrol and security",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NaTo1000/NiA-Cluster",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyserial>=3.5",
        "paramiko>=2.11.0",
        "pybluez>=0.23",
        "netifaces>=0.11.0",
        "cryptography>=3.4.8",
        "pyyaml>=6.0",
        "requests>=2.27.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
        "voice": [
            "SpeechRecognition>=3.8.1",
            "pyttsx3>=2.90",
        ],
        "email": [
            "smtplib",
        ],
    },
    entry_points={
        "console_scripts": [
            "nia-cluster=nia_cluster.cli:main",
        ],
    },
)
