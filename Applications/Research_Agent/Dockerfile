# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy application code
COPY . /app

# Create logs directory
RUN mkdir -p /app/logs

# Expose ports
EXPOSE 8000 8001

# Default command
CMD ["python", "src/web/manage.py", "runserver", "0.0.0.0:8000"]
