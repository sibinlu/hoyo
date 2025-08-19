# HoYoverse Daily Check-in Automation

Automated daily check-in for Genshin Impact, Honkai Star Rail, and Zenless Zone Zero.

## Setup

```bash
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

## Usage

```bash
# Run check-ins for all games
./bin/hoyo checkin

# Show help
./bin/hoyo help
```

## Configuration

Set environment variables to customize behavior:

```bash
export HOYO_ENABLED_GAMES="gi,hsr,zzz"    # Games to check (gi/hsr/zzz)
export SESSION_PATH="/secure/path"         # Session storage directory
export HOYO_HEADLESS="true"               # Headless browser mode
```

## First Run

The first run opens a browser for HoYoLab login. Complete authentication and close the browser to save your session.

## Project Structure

```
hoyo/
├── bin/hoyo          # Command-line interface
├── main.py           # Main application
├── auth/             # Authentication & session management
├── checkin/          # Game-specific check-in logic
└── venv/             # Virtual environment
```

## System-wide Installation

Add to your PATH or create symlink:

```bash
# Option 1: Add to PATH
export PATH="$PATH:/path/to/hoyo/bin"

# Option 2: Create symlink
sudo ln -s /path/to/hoyo/bin/hoyo /usr/local/bin/hoyo
```

Then use `hoyo checkin` from anywhere.