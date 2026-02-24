"""Setup script for WW2 ETL project."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split("\n")
    requirements = [r.strip() for r in requirements if r.strip() and not r.startswith("#")]

setup(
    name="ww2-etl",
    version="0.2.0",
    description="ETL pipeline for collecting and processing WW2 timeline data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Camilo Munoz",
    author_email="jucmunozar@gmail.com",
    url="https://github.com/jucmunozar/ww2-etl",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "ww2-etl=scripts.run_etl:main",
            "ww2-api=scripts.run_api:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
