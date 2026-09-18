FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Clone official SWE-agent
RUN git clone https://github.com/princeton-nlp/SWE-agent.git /swe-agent

# Install SWE-agent dependencies
WORKDIR /swe-agent
RUN pip install --no-cache-dir -e .

# Copy our wrapper script
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY run_swe_agent.py .
COPY config/ ./config/

CMD ["python", "run_swe_agent.py"]
