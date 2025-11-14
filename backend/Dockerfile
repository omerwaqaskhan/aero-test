# Multi-stage Dockerfile for WindWays Backend
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies (including Playwright dependencies)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        wget \
        gnupg \
        ca-certificates \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libwayland-client0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        xdg-utils \
        libu2f-udev \
        libvulkan1 \
        && rm -rf /var/lib/apt/lists/*

# Dependencies stage
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install -y --no-install-recommends fonts-unifont || true \
    && rm -rf /var/lib/apt/lists/* \
    && playwright install chromium

# Production stage
FROM base AS production
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
# Install Playwright browsers as root first
RUN playwright install chromium || true

# Copy application code
COPY auth_module/ ./auth_module/
COPY search_booking_module/ ./search_booking_module/
COPY pyproject.toml .
COPY setup.py .

# Create non-root user and set up Playwright cache
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /home/appuser/.cache/ms-playwright \
    && cp -r /root/.cache/ms-playwright/* /home/appuser/.cache/ms-playwright/ 2>/dev/null || true \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /home/appuser/.cache/ms-playwright || true
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "auth_module.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Development stage
FROM base AS development
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pytest pytest-asyncio pytest-cov black isort flake8 mypy \
    && apt-get update \
    && apt-get install -y --no-install-recommends fonts-unifont || true \
    && rm -rf /var/lib/apt/lists/* \
    && playwright install chromium

# Copy application code
COPY auth_module/ ./auth_module/
COPY search_booking_module/ ./search_booking_module/
COPY pyproject.toml .
COPY setup.py .

# Create non-root user and set up Playwright cache
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /home/appuser/.cache/ms-playwright \
    && cp -r /root/.cache/ms-playwright/* /home/appuser/.cache/ms-playwright/ 2>/dev/null || true \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /home/appuser/.cache/ms-playwright || true
USER appuser

# Expose port
EXPOSE 8000

# Run the application in development mode
CMD ["uvicorn", "auth_module.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
