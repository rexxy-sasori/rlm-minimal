# Dependencies Documentation

This document outlines all dependencies for the RLM Minimal project.

## Python Dependencies

### Core Dependencies (requirements.txt)

These are the main dependencies required to run the project:

```txt
# Core dependencies
openai>=1.0.0          # OpenAI API client
dotenv>=1.0.0          # Environment variable loading
rich>=13.7.0           # Rich text formatting for logging

# TimescaleDB dependencies (for logging and latency tracking)
psycopg2-binary>=2.9.9 # PostgreSQL adapter (for TimescaleDB)
python-dotenv>=1.0.0   # Environment variable loading (duplicate for clarity)
```

### Logger-Specific Dependencies (rlm/logger/requirements.txt)

These are the dependencies specifically for the logging module:

```txt
# Logger-specific dependencies
# These are also included in the main requirements.txt
psycopg2-binary>=2.9.9 # PostgreSQL adapter
python-dotenv>=1.0.0   # Environment variable loading
rich>=13.7.0           # Rich text formatting
```

## System Dependencies

### For Docker (Dockerfile)

These system packages are required for building and running the application:

```bash
# Required for compiling Python packages
gcc

# Required for psycopg2 (PostgreSQL adapter)
libpq-dev
```

### For Local Development

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y gcc libpq-dev python3-dev
```

#### macOS (using Homebrew):
```bash
brew install postgresql
```

#### Windows:
Download and install PostgreSQL from https://www.postgresql.org/download/windows/

## Installation

### Using pip:
```bash
pip install -r requirements.txt
```

### Using Docker:
```bash
docker build -t rlm-minimal:latest .
```

## Optional Dependencies

### For Development:
```bash
# Testing
pytest>=7.0.0
pytest-cov>=4.0.0

# Code formatting
black>=23.0.0
flake8>=6.0.0

# Type checking
mypy>=1.0.0
```

### For TimescaleDB:

If you want to run TimescaleDB locally:

#### Using Docker:
```bash
docker run -d --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  timescale/timescaledb:latest-pg16
```

#### Using Docker (manual):
```bash
docker run -d --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  timescale/timescaledb:latest-pg16

# Wait for database to be ready
docker exec -it timescaledb psql -U postgres -c "CREATE DATABASE rlm_logs;"

# Initialize schema
docker exec -i timescaledb psql -U postgres -d rlm_logs < rlm/logger/sql/timescale_schema.sql
```

## Environment Variables

### Required:
```env
OPENAI_API_KEY=your_openai_api_key
```

### Optional (for TimescaleDB logging):
```env
# TimescaleDB connection
TIMESCALE_DB_HOST=localhost
TIMESCALE_DB_PORT=5432
TIMESCALE_DB_NAME=rlm_logs
TIMESCALE_DB_USER=postgres
TIMESCALE_DB_PASSWORD=password

# LLM configuration
LLM_MODEL=gpt-4o
LLM_RECURSIVE_MODEL=gpt-5-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_RECURSIVE_BASE_URL=https://api.openai.com/v1
```

## Dependency Matrix

| Dependency | Version | Purpose | Required | Docker |
|------------|---------|---------|----------|--------|
| openai | >=1.0.0 | OpenAI API client | Yes | Yes |
| dotenv | >=1.0.0 | Environment variables | Yes | Yes |
| rich | >=13.7.0 | Rich logging | Yes | Yes |
| psycopg2-binary | >=2.9.9 | PostgreSQL adapter | No* | Yes |
| python-dotenv | >=1.0.0 | Environment variables | No* | Yes |
| gcc | - | Compiler | - | Yes |
| libpq-dev | - | PostgreSQL dev files | - | Yes |

* Required only if using TimescaleDB logging

## Notes

1. **psycopg2 vs psycopg2-binary**: We use `psycopg2-binary` for easier installation in Docker and CI/CD environments. For production, consider using `psycopg2` which requires PostgreSQL development libraries.

2. **Version Pinning**: We use minimum version requirements (`>=`) to allow for updates while maintaining compatibility.

3. **Duplicate Dependencies**: `python-dotenv` appears in both requirements files because `dotenv` and `python-dotenv` are actually the same package (python-dotenv is the canonical name).

4. **Docker Deployment**: See the Dockerfile for examples of running RLM with TimescaleDB using `docker run` commands.
