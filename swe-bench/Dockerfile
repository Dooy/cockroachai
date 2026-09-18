FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Clone and install SWE-agent
RUN git clone https://github.com/princeton-nlp/SWE-agent.git /swe-agent && \
    cd /swe-agent && \
    pip install --no-cache-dir -e .

# Install additional dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our wrapper script
COPY run_swe_agent.py .
RUN chmod +x run_swe_agent.py

# Create results directory
RUN mkdir -p /app/results

CMD ["python", "run_swe_agent.py"]
