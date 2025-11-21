FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install basic build deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only what's needed for installing dependencies first
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Expose ports
EXPOSE 8000

# Default envs (can be overridden with docker-compose or env_file)
ENV JOBS_DIR=/app/jobs
ENV WORKDIR=/app/runs
ENV LOG_DIR=/app/logs

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
