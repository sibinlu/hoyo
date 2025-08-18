#!/usr/bin/env python3
"""
HoyoLab Check-in Automation
Entry point for the application.
"""

from loguru import logger
from rich.console import Console
from rich.panel import Panel
import sys

from login import check_login_status

console = Console()

def main():
    """Main entry point for HoyoLab check-in automation."""
    try:
        console.print(Panel("🎮 HoyoLab Check-in Automation", style="bold blue"))
        
        # Check login status
        if not check_login_status():
            logger.error("Login required. Please complete authentication.")
            sys.exit(1)
        
        logger.info("Login verified successfully")
        console.print("✅ Authentication verified", style="green")
        
        # TODO: Add check-in functionality
        console.print("🚧 Check-in functionality coming soon...", style="yellow")
        
    except KeyboardInterrupt:
        console.print("\n⚠️  Operation cancelled by user", style="yellow")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

if __name__ == "__main__":
    main()