#!/bin/bash
set -e

echo "=== SWE-bench Lite Deployment Script ==="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your API key before continuing."
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_api_key_here" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not set in .env"
    exit 1
fi

echo "📦 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting SWE-bench Lite test..."
echo "Model: $MODEL_NAME"
echo "Tasks: $NUM_TASKS"
echo "Base URL: $ANTHROPIC_BASE_URL"
echo ""

docker-compose up

echo ""
echo "✅ Test complete! Check ./results directory for outputs."
