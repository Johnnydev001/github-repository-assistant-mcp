FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build tooling for editable install
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml /app/
COPY src/ /app/src/
COPY client/ /app/client/
COPY README.md /app/
COPY .env.example /app/

# Install Python deps and package
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir -e .

# Default entrypoint runs the client CLI. Pass the desired client subcommand as arguments to `docker run`.
ENTRYPOINT ["python", "client/cli.py"]
