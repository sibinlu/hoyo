#!/usr/bin/env python3
"""
HoyoLab Check-in Automation - Refactored Version
Entry point for the application with improved architecture.
"""

from rich.console import Console
from rich.table import Table
import sys
from typing import Dict

# Configure logging before other imports
from logging_config import setup_logging
setup_logging()

from loguru import logger
from auth.auth import check_login_status, load_session
from checkin.config import GAMES, Game, AppConfig, get_enabled_games
from checkin.exceptions import CheckinResult, get_result_display_info
from checkin.gi_checkin import GenshinImpactCheckin
from checkin.hsr_checkin import HonkaiStarRailCheckin
from checkin.zzz_checkin import ZenlessZoneZeroCheckin

console = Console()

# Game checkin classes mapping
CHECKIN_CLASSES = {
    Game.GI: GenshinImpactCheckin,
    Game.HSR: HonkaiStarRailCheckin,
    Game.ZZZ: ZenlessZoneZeroCheckin,
}

def perform_game_checkin(game: Game, app_config: AppConfig, session_data: dict) -> CheckinResult:
    """
    Perform check-in for a specific game.
    
    Args:
        game: The game to perform check-in for
        app_config: Application configuration
        session_data: Session data for authentication
        
    Returns:
        CheckinResult indicating the outcome
    """
    try:
        checkin_class = CHECKIN_CLASSES[game]
        checkin = checkin_class(app_config, session_data)
        return checkin.perform_checkin()
    except Exception as e:
        logger.error(f"Failed to perform {game.value} check-in: {e}")
        console.print(f"❌ {GAMES[game].name} check-in failed: {e}", style="red")
        return CheckinResult.FAILED

def create_summary_table(results: Dict[Game, CheckinResult]) -> Table:
    """
    Create a beautiful summary table of check-in results.
    
    Args:
        results: Dictionary mapping games to their results
        
    Returns:
        Rich Table object
    """
    table = Table(title="📊 Daily Check-in Summary", show_header=True, header_style="bold magenta")
    table.add_column("Game", style="bold", width=20)
    table.add_column("Status", justify="center", width=15)
    table.add_column("Message", width=30)
    
    for game, result in results.items():
        game_config = GAMES[game]
        status_text, message, color = get_result_display_info(result)
        
        table.add_row(
            game_config.name,
            f"[{color}]{status_text}[/{color}]",
            f"[{color}]{message}[/{color}]"
        )
    
    return table

def calculate_success_summary(results: Dict[Game, CheckinResult]) -> tuple:
    """
    Calculate success statistics from results.
    
    Args:
        results: Dictionary mapping games to their results
        
    Returns:
        Tuple of (successful_count, total_count)
    """
    successful_results = {CheckinResult.SUCCESS, CheckinResult.ALREADY_CHECKED_IN}
    successful_count = sum(1 for result in results.values() if result in successful_results)
    total_count = len(results)
    
    return successful_count, total_count

def main():
    """Main entry point for HoyoLab check-in automation."""
    try:
        # Load application configuration
        app_config = AppConfig.from_env()
        
        # Check login status
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
        
        # Get enabled games
        enabled_games = get_enabled_games()
        logger.info(f"Enabled games: {[game.value for game in enabled_games]}")
        
        results = {}
        for game in enabled_games:
            if game in GAMES:
                console.print(f"\n{GAMES[game].name} Check-in")
                result = perform_game_checkin(game, app_config, session_data)
                results[game] = result
            else:
                logger.warning(f"Unknown game: {game}")
                results[game] = CheckinResult.FAILED
        
        # Create and display summary table
        if results:
            table = create_summary_table(results)
            console.print("\n")
            console.print(table)
            
            # Overall summary
            successful_count, total_count = calculate_success_summary(results)
            
            if successful_count == total_count:
                console.print("\n🎉 All check-ins completed successfully!", style="bold green")
            elif successful_count > 0:
                console.print(f"\n⚠️  {successful_count}/{total_count} check-ins completed", style="bold yellow")
            else:
                console.print("\n💥 All check-ins failed", style="bold red")
        else:
            console.print("⚠️  No games enabled for check-in", style="yellow")
        
    except KeyboardInterrupt:
        console.print("\n⚠️  Operation cancelled by user", style="yellow")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

if __name__ == "__main__":
    main()