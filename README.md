# HoYoverse Automation

Automates daily check-ins and code redemption for Genshin Impact, Honkai Star Rail, and Zenless Zone Zero.

## Setup

Requires Python 3.11+

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

## Usage

```bash
./bin/hoyo checkin redeem    # Check-in + redeem codes
./bin/hoyo checkin           # Check-in only  
./bin/hoyo redeem            # Redeem codes only
./bin/hoyo help              # Show help
```

## Features

- **Daily Check-ins**: Automated check-ins for all games
- **Code Redemption**: Auto-search and redeem HoYoLab codes  
- **Duplicate Prevention**: Tracks redeemed codes locally
- **Multi-command**: Run multiple operations in sequence

## Configuration

```bash
export HOYO_ENABLED_GAMES="gi,hsr,zzz"    # Games to enable
export HOYO_HEADLESS="true"               # Headless mode
```

## System Install

```bash
# Add to PATH
export PATH="$PATH:/path/to/hoyo/bin"

# Or create symlink  
sudo ln -s /path/to/hoyo/bin/hoyo /usr/local/bin/hoyo
```

First run opens browser for HoYoLab login authentication.

## Docker Usage

### Setup

1. **Authenticate locally first** (one-time setup):
   ```bash
   # Use local installation to authenticate (opens browser)
   ./bin/hoyo auth
   ```
   This creates session data in `./checkin/` which will be shared with Docker.

2. Copy the environment example file (optional):
   ```bash
   cp .env.example .env
   # Edit .env if you need to add environment variables
   ```

3. Build the Docker image:
   ```bash
   docker-compose build
   ```

### Running with Docker

Run check-in and code redemption:
```bash
docker-compose run --rm hoyo checkin redeem
```

Run check-in only:
```bash
docker-compose run --rm hoyo checkin
```

Run code redemption only:
```bash
docker-compose run --rm hoyo redeem
```

**Note**:
- `--rm` automatically removes the container after it completes, keeping your system clean
- Docker uses the session data created during local authentication
- Re-run `./bin/hoyo auth` locally if authentication expires

### Benefits of Docker

- **Isolated Environment**: No conflicts with system dependencies
- **Reproducible**: Same environment every time
- **Portable**: Works on any system with Docker
- **Perfect for Scheduling**: Each run starts fresh and cleans up automatically
- **Real-time Output**: All Python stdout/stderr displayed in your terminal

### Persistent Data

Docker mounts these directories/files to persist data between runs:
- `./checkin/` - Authentication session data (hoyo_session_data.json)
- `./logs/` - Application logs
- `./redeemed_codes.json` - Tracks redeemed codes

### Security Notes

- `.env` file is gitignored and never committed
- Store sensitive credentials in `.env` file only
- Session data is stored locally and mounted into container

## Scheduled Automation (Prefect)

For automated scheduled execution using Prefect:

- **Weekly Authentication**: Renews session every Sunday at 2 AM
- **Daily Check-in**: Runs check-in and redemption every day at 10 AM

See [deploy/README.md](deploy/README.md) for Prefect deployment setup and usage.