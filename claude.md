# Project

## Tech Stack
- Python + Playwright for automation
- Loguru for logging
- Rich for CLI output
- Use python 3.11 venv
- Update requirement.txt whenever there is a new plugin.

## Development Guidelines
- Use Playwright codegen for browser related generation.
- Keep main.py clean and minimal.
- No co-author in git commits.
- All py file should be less than 600 lines. 
- Auto Capsulate similar functions. 
- If login is required, popup for user to enter and save the cookie and other data for future use. These data should be in gitignore. 

## Architecture
- Modular design with separated concerns
- Configuration-driven approach
- Robust error handling and logging 