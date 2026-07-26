FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for scientific libraries & build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ backend/

# Set Python path so app modules import cleanly
ENV PYTHONPATH=/app/backend

# Expose port (default 8000)
EXPOSE 8000

# Command to run uvicorn server in production mode (respecting dynamic PORT on cloud hosts)
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
