FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install official SWE-agent
RUN pip install --no-cache-dir sweagent

# Copy our wrapper script
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY run_swe_agent.py .
COPY config/ ./config/

CMD ["python", "run_swe_agent.py"]
