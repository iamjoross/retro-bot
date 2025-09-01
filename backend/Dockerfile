FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Update packages and remove package lists to reduce attack surface
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Create cache directory and set permissions
RUN mkdir -p /home/appuser/.cache/huggingface && \
    chown -R appuser:appuser /home/appuser/.cache

WORKDIR /app

# Install dependencies as root (required for pip)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application and change ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Use non-privileged port
EXPOSE 8000

# Default to production mode, override in docker-compose for dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]