# Hoyo Checkin Project

## Tech Stack
- Python + Playwright for automation
- Loguru for logging
- Rich for CLI output

## Development Guidelines
- Use Playwright codegen for test generation
- Keep main.py clean and minimal
- No co-author in git commits

## Architecture
- Modular design with separated concerns
- Configuration-driven approach
- Robust error handling and logging 

## Structure
1. main.py, the entry to run the task. 
2. login.py, check if the user has login in https://www.hoyolab.com/home. If not, open the page for user so he could login, then save the session for later use. 