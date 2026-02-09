#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Hoyo Deployment Setup"
echo "======================="

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    else
        echo "Creating new .env file..."
        touch "$PROJECT_ROOT/.env"
    fi
fi

# Check for PREFECT_BIN in .env
if ! grep -q "^PREFECT_BIN=" "$PROJECT_ROOT/.env" 2>/dev/null || [ -z "$(grep "^PREFECT_BIN=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)" ]; then
    echo -e "${YELLOW}⚠️  PREFECT_BIN not set in .env${NC}"
    echo -n "Enter path to Prefect binary (e.g., ~/project/housework/prefect/prefect-env/bin/prefect): "
    read PREFECT_BIN

    # Expand ~ to full path
    PREFECT_BIN=$(eval echo "$PREFECT_BIN")

    if [ ! -f "$PREFECT_BIN" ]; then
        echo -e "${RED}❌ Prefect binary not found at: $PREFECT_BIN${NC}"
        exit 1
    fi

    # Add to .env
    echo "PREFECT_BIN=$PREFECT_BIN" >> "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✓ PREFECT_BIN added to .env${NC}"
fi

# Source .env to get PREFECT_BIN
export $(grep "^PREFECT_BIN=" "$PROJECT_ROOT/.env" | xargs)
PREFECT_BIN=$(eval echo "$PREFECT_BIN")

# Get Python from the same directory as prefect binary
PREFECT_PYTHON="$(dirname "$PREFECT_BIN")/python"

echo -e "\n📦 Setting up Python virtual environment..."

# Create venv if it doesn't exist
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv "$PROJECT_ROOT/venv"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate venv and install requirements
echo "Installing Python dependencies..."
source "$PROJECT_ROOT/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$PROJECT_ROOT/requirements.txt"
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Check if Playwright browsers are installed
echo -e "\n🌐 Checking Playwright browsers..."

# Determine cache location (macOS vs Linux)
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLAYWRIGHT_CACHE="$HOME/Library/Caches/ms-playwright"
else
    PLAYWRIGHT_CACHE="$HOME/.cache/ms-playwright"
fi

# Check if browsers exist
if [ ! -d "$PLAYWRIGHT_CACHE" ] || [ -z "$(ls -A "$PLAYWRIGHT_CACHE" 2>/dev/null)" ]; then
    echo "Installing Playwright browsers (this may take a few minutes)..."
    python -m playwright install chromium
    echo -e "${GREEN}✓ Playwright browsers installed${NC}"
else
    echo -e "${GREEN}✓ Playwright browsers already installed${NC}"
fi

# Update .env with cache path if not set
if ! grep -q "^PLAYWRIGHT_CACHE=" "$PROJECT_ROOT/.env" 2>/dev/null; then
    echo "PLAYWRIGHT_CACHE=$PLAYWRIGHT_CACHE" >> "$PROJECT_ROOT/.env"
fi

echo -e "\n📅 Deploying to Prefect..."

# Check if Python exists in the same directory
if [ ! -f "$PREFECT_PYTHON" ]; then
    echo -e "${RED}❌ Python not found at: $PREFECT_PYTHON${NC}"
    exit 1
fi

# Use Prefect's Python to deploy
"$PREFECT_PYTHON" "$PROJECT_ROOT/deploy/prefect_deployment.py"
echo -e "${GREEN}✓ Deployment registered with Prefect${NC}"

echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Make sure Prefect worker is running: prefect worker start --pool personal-pool"
echo "  2. View deployments: prefect deployment ls"
echo "  3. Trigger manually: prefect deployment run hoyo-daily-flow"
echo ""
echo "Note: Docker is optional. The Prefect flow uses the local binary."
echo "To build Docker image: docker-compose build"
echo ""
