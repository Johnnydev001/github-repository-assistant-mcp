FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV LOCAL_SOURCE_DIR=/app/server/local_source 
RUN mkdir -p "${LOCAL_SOURCE_DIR}" && chown -R root:root "${LOCAL_SOURCE_DIR}"

# Set working dir to server package location so pip install . finds pyproject.toml
WORKDIR /app

# Install build tooling for building the package
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

# Copy the server package directory (pyproject + src) into the image
COPY . /app/server/

# Install dependencies and the package (non-editable for reproducible installs)
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir /app/server

# Default entrypoint runs the installed console_script created by pyproject
ENTRYPOINT ["portfolio-mcp-server"]
