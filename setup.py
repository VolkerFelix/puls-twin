from setuptools import setup, find_packages

setup(
    name="pulstwin",
    version="0.1.0",
    description="Wearable-driven digital twin system using Pulse Engine",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.20.0",
        "protobuf>=3.19.0",
        # "pulse" should be listed here if it were installable via pip
        # Since it's likely a custom installation, we'll exclude it
    ],
    python_requires=">=3.6",
)