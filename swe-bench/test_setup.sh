#!/bin/bash
# Test setup before running full benchmark

set -e

echo "🔍 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi
echo "✓ Docker found: $(docker --version)"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose v2+"
    exit 1
fi
echo "✓ Docker Compose found: $(docker compose version)"

# Check .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example and configure it."
    exit 1
fi
echo "✓ .env file exists"

# Load and check environment variables
source .env

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY not set in .env"
    exit 1
fi
echo "✓ ANTHROPIC_API_KEY is set"

if [ -z "$ANTHROPIC_BASE_URL" ]; then
    echo "⚠ ANTHROPIC_BASE_URL not set, using default"
fi

echo "✓ Model: ${MODEL:-claude-opus-5}"
echo "✓ Tasks: ${NUM_TASKS:-2}"

# Test API connection
echo ""
echo "🌐 Testing API connection..."
if command -v curl &> /dev/null; then
    if curl -s --max-time 5 "$ANTHROPIC_BASE_URL" > /dev/null 2>&1; then
        echo "✓ API endpoint reachable"
    else
        echo "⚠ Cannot reach API endpoint (might be normal if it requires auth)"
    fi
fi

# Check disk space
echo ""
echo "💾 Checking disk space..."
AVAILABLE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE" -lt 10 ]; then
    echo "⚠ Warning: Less than 10GB available disk space"
else
    echo "✓ Sufficient disk space: ${AVAILABLE}GB available"
fi

# Check memory
echo ""
echo "🧠 Checking memory..."
if command -v free &> /dev/null; then
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 4 ]; then
        echo "⚠ Warning: Less than 4GB total memory"
    else
        echo "✓ Sufficient memory: ${TOTAL_MEM}GB total"
    fi
fi

echo ""
echo "✅ All checks passed! Ready to run ./deploy.sh"
