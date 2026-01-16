# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
# - gcc: For compiling Python packages
# - libpq-dev: For psycopg2 (PostgreSQL adapter)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.sh scripts/*.py

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Default command (can be overridden)
CMD ["python", "main.py"]

# Dataset setup command (can be used during build or runtime)
# docker build --build-arg SETUP_DATASETS=true -t rlm-minimal:latest .
ARG SETUP_DATASETS=false
RUN if [ "$SETUP_DATASETS" = "true" ]; then \
    python scripts/setup_datasets.py --dataset all; \
fi

# Example run command:
# docker run -e OPENAI_API_KEY="sk-xxx" rlm-minimal
# 
# With full configuration:
# docker run \
#   -e OPENAI_API_KEY="sk-xxx" \
#   -e LLM_MODEL="gpt-4o" \
#   -e LLM_RECURSIVE_MODEL="gpt-5-mini" \
#   -e LLM_RECURSIVE_BASE_URL="http://host.docker.internal:1234/v1" \
#   rlm-minimal
#
# With TimescaleDB logging:
# docker run \
#   -e OPENAI_API_KEY="sk-xxx" \
#   -e TIMESCALE_DB_HOST="timescaledb" \
#   -e TIMESCALE_DB_PORT="5432" \
#   -e TIMESCALE_DB_NAME="rlm_logs" \
#   -e TIMESCALE_DB_USER="postgres" \
#   -e TIMESCALE_DB_PASSWORD="password" \
#   --network=your-network \
#   rlm-minimal
