FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /tests

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy test files
COPY tests /tests
COPY captures /captures
COPY logs /logs

# Set environment variables
ENV PYTHONPATH=/tests
ENV PYTHONUNBUFFERED=1

# Default command - install CA certificates and keep container running
CMD ["python3", "/tests/install_proxy_cas.py", "--auto"]
