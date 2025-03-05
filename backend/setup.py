from setuptools import setup, find_packages

setup(
    name="pitch-deck-analyzer-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "redis",
        "rq",
        "requests",
        "pytest",
    ],
) 