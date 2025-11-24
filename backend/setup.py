"""Setup script for the Trivago Auth module."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="luftway-auth",
    version="1.0.0",
    author="Luftway Team",
    author_email="team@luftway.com",
    description="Multi-tenant authentication and authorization module for Luftway travel platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/luftway/auth-module",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Security",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "factory-boy>=3.3.0",
            "faker>=20.1.0",
        ],
        "sms": [
            "twilio>=8.10.0",
            "boto3>=1.34.0",
        ],
        "monitoring": [
            "structlog>=23.2.0",
            "prometheus-client>=0.19.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "luftway-auth=auth_module.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "auth_module": [
            "migrations/*",
            "migrations/versions/*",
        ],
    },
)
