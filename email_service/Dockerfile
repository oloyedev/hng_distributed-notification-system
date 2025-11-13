FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install OS deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements if present and install
COPY requirements.txt ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy app source
COPY . /app

# Expose port
EXPOSE 3003

# Default command
CMD ["python", "main.py"]
