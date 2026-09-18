#!/bin/bash
set -e

echo "=================================="
echo "SWE-agent with Claude Opus 5"
echo "=================================="

# Check .env file
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Load environment variables
source .env

# Validate required variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY not set in .env"
    exit 1
fi

echo "Model: ${MODEL:-claude-opus-5}"
echo "Tasks: ${NUM_TASKS:-2}"
echo ""

# Build and run
echo "Building Docker image (this may take a while on first run)..."
docker compose build

echo ""
echo "Starting SWE-agent..."
echo "This will take a while (each task ~5-15 minutes)..."
echo ""

docker compose up

echo ""
echo "=================================="
echo "Results saved to ./results/"
echo "=================================="
