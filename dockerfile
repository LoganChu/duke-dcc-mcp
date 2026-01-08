FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_suggest_server.py .
COPY otel_instrument.py .

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

# Create required directories
RUN mkdir -p /tmp /app/logs && \
    chown -R mcp:mcp /tmp /app/logs

USER mcp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "mcp_suggest_server:app", "--host", "0.0.0.0", "--port", "8000"]