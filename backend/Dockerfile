# =============================================================================
# Legatio AI — Backend Dockerfile
# =============================================================================

FROM python:3.12-slim AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/development.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Default: Daphne (ASGI) so HTTP + WebSockets work the same in every environment.
# docker-compose may override the command for local convenience.
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "legatio.asgi:application"]
