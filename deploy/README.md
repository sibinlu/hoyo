# Hoyo Deployment Guide

## Overview

This deployment setup allows you to run Hoyo automation via Prefect on any server. The workflow:
1. Pull code from git
2. Run `deploy/start.sh`
3. Script sets up everything and registers with Prefect

## Architecture

- **Docker**: Containerizes the Hoyo app (no browsers inside - only 762MB!)
- **Playwright Browsers**: Shared cache on host system (~300MB)
- **Prefect**: External installation manages scheduling (e.g., `~/project/housework/prefect`)
- **Workflow**: auth → checkin → redeem (runs daily)

## Quick Start

### On a New Server

```bash
# Clone the repository
git clone <your-repo-url> ~/project/hoyo
cd ~/project/hoyo

# Run deployment script
./deploy/start.sh
```

The script will:
1. Create `.env` if missing
2. Prompt for `PREFECT_PATH` if not set
3. Create Python 3.11 venv
4. Install dependencies from requirements.txt
5. Install Playwright browsers to shared cache (if needed)
6. Build Docker image
7. Register deployment with Prefect

### Prerequisites

- Docker and docker-compose installed
- Python 3.11 installed
- Prefect installation with `personal-pool` worker configured
- Git (for pulling code)

## Environment Variables

Create a `.env` file in the project root:

```bash
# Path to external Prefect installation (REQUIRED)
PREFECT_PATH=~/project/housework/prefect

# Optional: Custom session data path
SESSION_DATA_PATH=~/SessionData

# Optional: Custom Playwright cache path (auto-detected by default)
# macOS: ~/Library/Caches/ms-playwright
# Linux: ~/.cache/ms-playwright
PLAYWRIGHT_CACHE=~/.cache/ms-playwright
```

## Docker Image Details

**New optimized image: ~762MB** (reduced from 2GB!)

Breakdown:
- Base Python 3.11: ~109MB
- System dependencies: ~228MB (runtime libs for Chromium)
- Python packages: ~183MB
- Your code: ~500KB
- **No browsers inside** - mounted from host

The Docker image is portable but requires:
- Playwright browser cache mounted from host
- Session data mounted from host

## File Structure

```
hoyo/
├── deploy/
│   ├── start.sh                    # Main deployment script
│   ├── prefect_deployment.py       # Prefect flow definition
│   └── README.md                   # This file
├── Dockerfile                      # Optimized Docker image (Python 3.11)
├── docker-compose.yml              # Docker setup with volume mounts
├── requirements.txt                # Python dependencies (no Prefect)
├── .env                            # Environment configuration
└── bin/hoyo                        # Local binary
```

## Deployment Schedule

- **Flow name**: `hoyo-daily-flow`
- **Schedule**: Daily at 10:00 AM Pacific Time
- **Worker pool**: `personal-pool`
- **Steps**:
  1. Run `hoyo auth` (refresh session)
  2. Run `hoyo checkin redeem` (daily tasks)

## Manual Operations

### Run flow manually
```bash
prefect deployment run hoyo-daily-flow
```

### View deployments
```bash
prefect deployment ls
```

### Test locally
```bash
# Run full flow locally
./bin/hoyo auth
./bin/hoyo checkin redeem

# Or test Docker container (for checkin/redeem only)
docker-compose run --rm hoyo checkin redeem
```

### Rebuild Docker image
```bash
docker-compose build --no-cache
```

### Update deployment
```bash
cd ~/project/hoyo
git pull
./deploy/start.sh
```

## Troubleshooting

### Issue: Prefect deployment fails
- Check `PREFECT_PATH` is correct in `.env`
- Verify Prefect venv exists at `$PREFECT_PATH/venv`
- Ensure Prefect worker is running: `prefect worker start --pool personal-pool`

### Issue: Docker build fails
- Ensure Python 3.11 is available
- Check internet connection for package downloads
- Try: `docker-compose build --no-cache`

### Issue: Playwright browsers not found
```bash
# Install browsers manually
source venv/bin/activate
python -m playwright install chromium
```

### Issue: Auth fails
- Auth requires browser interaction, must run locally: `./bin/hoyo auth`
- Auth cannot run in Docker (no display)
- Session is saved and mounted into Docker for checkin/redeem

### Issue: start.sh fails
```bash
# Make sure it's executable
chmod +x deploy/start.sh

# Run with bash explicitly
bash deploy/start.sh
```

## Platform Differences

### macOS
- Playwright cache: `~/Library/Caches/ms-playwright`
- Docker Desktop native

### Linux
- Playwright cache: `~/.cache/ms-playwright`
- May need Docker group permissions: `sudo usermod -aG docker $USER`

## Security Notes

- `.env` file contains sensitive paths - keep it in `.gitignore`
- Session data contains authentication cookies - keep it secure
- Playwright browsers are mounted read-only into Docker
- Docker container has no network access except what's needed

## Advanced Configuration

### Change schedule
Edit `deploy/prefect_deployment.py`:
```python
schedule=Cron("0 10 * * *", timezone="America/Los_Angeles")
```

Then redeploy:
```bash
./deploy/start.sh
```

### Use different worker pool
Edit `deploy/prefect_deployment.py`:
```python
work_pool_name="your-pool-name"
```

### Custom session path
Add to `.env`:
```bash
SESSION_DATA_PATH=/custom/path/to/session
```

## Key Design Decisions

1. **Prefect is external** - Not in requirements.txt, managed separately
2. **Browsers on host** - Shared cache, not in Docker image
3. **Auth runs locally** - Needs browser interaction
4. **Docker for portability** - Code + deps containerized
5. **Python 3.11** - Stable, good package compatibility

## Notes

- **DO NOT** run auth in Docker (requires browser interaction)
- Session data is mounted from host into container
- Browsers are shared between host and container
- Docker image is portable but requires host browser cache
- Prefect must be installed separately (external project)
- The deployment script handles everything automatically
