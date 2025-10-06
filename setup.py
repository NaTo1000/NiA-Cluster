from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nia-cluster",
    version="1.0.0",
    author="NiA",
    description="Advanced networking cluster tool with AI integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NaTo1000/NiA-Cluster",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.8",
    install_requires=[
        "asyncio-mqtt>=0.16.1",
        "paramiko>=3.4.0",
        "pyserial>=3.5",
        "bleak>=0.21.1",
        "esptool>=4.7.0",
        "netifaces>=0.11.0",
        "scapy>=2.5.0",
        "SpeechRecognition>=3.10.0",
        "pyttsx3>=2.90",
        "psutil>=5.9.0",
        "pyyaml>=6.0",
        "cryptography>=41.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "nia-cluster=nia_cluster.cli:main",
        ],
    },
)
