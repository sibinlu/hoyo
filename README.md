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