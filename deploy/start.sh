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

# Check for PREFECT_PATH in .env
if ! grep -q "^PREFECT_PATH=" "$PROJECT_ROOT/.env" 2>/dev/null || [ -z "$(grep "^PREFECT_PATH=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)" ]; then
    echo -e "${YELLOW}⚠️  PREFECT_PATH not set in .env${NC}"
    echo -n "Enter path to Prefect installation (e.g., ~/project/housework/prefect): "
    read PREFECT_PATH

    # Expand ~ to full path
    PREFECT_PATH=$(eval echo "$PREFECT_PATH")

    if [ ! -d "$PREFECT_PATH" ]; then
        echo -e "${RED}❌ Directory does not exist: $PREFECT_PATH${NC}"
        exit 1
    fi

    # Add to .env
    echo "PREFECT_PATH=$PREFECT_PATH" >> "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✓ PREFECT_PATH added to .env${NC}"
fi

# Source .env to get PREFECT_PATH
export $(grep "^PREFECT_PATH=" "$PROJECT_ROOT/.env" | xargs)
PREFECT_PATH=$(eval echo "$PREFECT_PATH")

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

echo -e "\n🐳 Building Docker image..."
docker-compose build
echo -e "${GREEN}✓ Docker image built${NC}"

echo -e "\n📅 Deploying to Prefect..."

# Check if Prefect venv exists
if [ ! -d "$PREFECT_PATH/venv" ]; then
    echo -e "${RED}❌ Prefect venv not found at: $PREFECT_PATH/venv${NC}"
    exit 1
fi

# Use Prefect's Python to deploy
"$PREFECT_PATH/venv/bin/python" "$PROJECT_ROOT/deploy/prefect_deployment.py"
echo -e "${GREEN}✓ Deployment registered with Prefect${NC}"

echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Make sure Prefect worker is running: prefect worker start --pool personal-pool"
echo "  2. View deployments: prefect deployment ls"
echo "  3. Trigger manually: prefect deployment run hoyo-daily-flow"
echo ""
