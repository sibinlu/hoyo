#!/usr/bin/env python3
"""
HoyoLab Check-in Automation - Refactored Version
Entry point for the application with improved architecture.
"""

from rich.console import Console
import sys

# Configure logging before other imports
from logging_config import setup_logging
setup_logging()

from loguru import logger
from auth.auth import check_login_status, load_session, wait_for_login_and_close
from auth.secure_session import get_session_manager
from checkin.checkin import main_checkin
from redeem.main import main_redeem

console = Console()

def show_help():
    """Display help information."""
    console.print("🎮 HoYoLab Automation Commands", style="bold blue")
    console.print("\nUsage: hoyo [command1] [command2] ...")
    console.print("\nAvailable commands:")
    console.print("  checkin  - Perform daily check-ins for all enabled games")
    console.print("  redeem   - Search and redeem available codes")
    console.print("  auth     - Remove existing auth data and redo authentication")
    console.print("  help     - Show this help message")
    console.print("\nExamples:")
    console.print("  hoyo checkin")
    console.print("  hoyo redeem") 
    console.print("  hoyo auth")
    console.print("  hoyo checkin redeem")
    console.print("  hoyo redeem checkin")

def handle_auth():
    """Handle authentication renewal by clearing existing session and re-authenticating."""
    console.print("🔐 Renewing authentication...", style="bold cyan")
    
    # Clear existing session data
    session_manager = get_session_manager()
    if session_manager.clear_session():
        console.print("✅ Existing auth data cleared", style="green")
    else:
        console.print("⚠️ Failed to clear existing auth data", style="yellow")
    
    # Initiate new authentication
    console.print("🔑 Starting new authentication process...", style="cyan")
    if wait_for_login_and_close():
        console.print("✅ Authentication completed successfully", style="green")
        return True
    else:
        console.print("❌ Authentication failed", style="red")
        return False


def main():
    """Main entry point for HoyoLab automation."""
    try:
        # Parse command line arguments - support multiple commands
        commands = sys.argv[1:] if len(sys.argv) > 1 else ["redeem"]
        
        # Handle help command
        if "help" in commands:
            show_help()
            return
        
        # Validate all commands
        valid_commands = ["checkin", "redeem", "auth"]
        for command in commands:
            if command not in valid_commands:
                console.print(f"❌ Unknown command: {command}", style="red")
                console.print("Use 'hoyo help' for available commands", style="yellow")
                sys.exit(1)
        
        # Handle auth command separately (doesn't need existing authentication)
        if "auth" in commands:
            if len(commands) == 1:
                # Only auth command, handle it and exit
                if handle_auth():
                    console.print("🎉 Authentication renewal completed!", style="bold green")
                else:
                    console.print("❌ Authentication renewal failed", style="bold red")
                    sys.exit(1)
                return
            else:
                console.print("❌ 'auth' command cannot be combined with other commands", style="red")
                console.print("Please run 'hoyo auth' separately", style="yellow")
                sys.exit(1)
        
        # Check login status for other commands
        if not check_login_status():
            logger.error("Login required. Please complete authentication.")
            sys.exit(1)
        
        logger.info("Login verified successfully")
        console.print("✅ Authentication verified", style="green")
        
        # Load session data
        session_data = load_session()
        if not session_data:
            logger.error("No session data found. Please login first.")
            console.print("❌ No session data found. Please login first.", style="red")
            sys.exit(1)
        
        # Execute commands in sequence
        for i, command in enumerate(commands):
            if i > 0:
                console.print(f"\n{'='*50}", style="dim")
            
            if command == "checkin":
                console.print("🎮 Starting HoYoLab Check-in Automation...", style="bold cyan")
                main_checkin(session_data)
            elif command == "redeem":
                console.print("🎁 Starting HoYoLab Code Redemption...", style="bold cyan")
                main_redeem(session_data)
        
        console.print(f"\n🎉 All operations completed successfully!", style="bold green")
        
    except KeyboardInterrupt:
        console.print("\n⚠️  Operation cancelled by user", style="yellow")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

if __name__ == "__main__":
    main()