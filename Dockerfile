# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Default command (can be overridden)
CMD ["python", "main.py"]

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
