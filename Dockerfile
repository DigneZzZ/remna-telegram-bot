# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application files with proper ownership
COPY --chown=botuser:botuser . .

# Create directory for logs
RUN mkdir -p /app/logs && chown botuser:botuser /app/logs

# Switch to non-root user
USER botuser

# Health check - simple ping to Telegram API
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import os; import requests; requests.get(f'https://api.telegram.org/bot{os.getenv(\"TELEGRAM_BOT_TOKEN\")}/getMe', timeout=5)" || exit 1

# Add labels
LABEL org.opencontainers.image.title="Remnawave Admin Bot"
LABEL org.opencontainers.image.description="Telegram bot for managing Remnawave VPN service"
LABEL org.opencontainers.image.source="https://github.com/dignezzz/remna-telegram-bot"
LABEL org.opencontainers.image.vendor="dignezzz"

# Run the application
CMD ["python", "main.py"]
