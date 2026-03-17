from setuptools import setup, find_packages

setup(
    name="tender-crawler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "playwright",
        "beautifulsoup4",
        "requests",
        "python-dateutil"
    ],
    python_requires=">=3.8",
    description="A web scraping tool for tender listings",
    author="Your Name",
    author_email="your.email@example.com",
)
