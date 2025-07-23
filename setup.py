#!/usr/bin/env python3
"""
Setup script for Virtuoso Gem Hunter
"""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="virtuoso-gem-hunter",
    version="1.0.0",
    author="Virtuoso Trading Systems",
    author_email="dev@virtuoso-trading.com",
    description="High-performance token discovery system for Solana with sophisticated gem hunting capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/virtuoso-trading/virtuoso-gem-hunter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "coverage>=6.0",
        ],
        "testing": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-mock>=3.6.0",
            "responses>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "virtuoso-gem-hunter=scripts.monitor:main",
        ],
    },
    keywords=[
        "solana",
        "token",
        "cryptocurrency", 
        "defi",
        "trading",
        "birdeye",
        "api-optimization",
        "batch-processing",
        "early-detection",
        "monitoring",
        "alerts",
        "telegram",
        "performance",
        "caching",
    ],
    project_urls={
        "Bug Reports": "https://github.com/virtuoso-trading/virtuoso-gem-hunter/issues",
        "Source": "https://github.com/virtuoso-trading/virtuoso-gem-hunter",
        "Documentation": "https://github.com/virtuoso-trading/virtuoso-gem-hunter/blob/main/docs/",
        "Funding": "https://github.com/sponsors/virtuoso-trading",
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.md", "*.txt", "*.sh"],
        "config": ["*.yaml", "*.yml"],
        "docs": ["*.md"],
    },
    zip_safe=False,
) 