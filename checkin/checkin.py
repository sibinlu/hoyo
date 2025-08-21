"""
Main checkin orchestration module
Handles daily check-ins for all enabled HoYoverse games
"""

from typing import Dict
from rich.console import Console
from rich.table import Table
from loguru import logger

from checkin.config import GAMES, Game, CheckinConfig, get_enabled_games
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


def perform_game_checkin(game: Game, checkin_config: CheckinConfig, session_data: dict) -> CheckinResult:
    """
    Perform check-in for a specific game.
    
    Args:
        game: The game to perform check-in for
        checkin_config: Check-in configuration
        session_data: Session data for authentication
        
    Returns:
        CheckinResult indicating the outcome
    """
    try:
        checkin_class = CHECKIN_CLASSES[game]
        checkin = checkin_class(checkin_config, session_data)
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


def display_final_summary(successful_count: int, total_count: int):
    """Display the final summary of all check-ins."""
    if successful_count == total_count:
        console.print("\n🎉 All check-ins completed successfully!", style="bold green")
    elif successful_count > 0:
        console.print(f"\n⚠️  {successful_count}/{total_count} check-ins completed", style="bold yellow")
    else:
        console.print("\n💥 All check-ins failed", style="bold red")


def run_daily_checkins(checkin_config: CheckinConfig, session_data: dict) -> Dict[Game, CheckinResult]:
    """
    Run check-in automation for all enabled games.
    
    Args:
        checkin_config: Check-in configuration
        session_data: Session data for authentication
        
    Returns:
        Dictionary mapping games to their check-in results
    """
    enabled_games = get_enabled_games()
    logger.info(f"Enabled games: {[game.value for game in enabled_games]}")
    
    console.print("\n📅 Starting daily check-ins...", style="cyan")
    
    results = {}
    for game in enabled_games:
        if game in GAMES:
            console.print(f"\n{GAMES[game].name} Check-in")
            result = perform_game_checkin(game, checkin_config, session_data)
            results[game] = result
        else:
            logger.warning(f"Unknown game: {game}")
            results[game] = CheckinResult.FAILED
    
    return results


def main_checkin(session_data: dict):
    """
    Main function to run check-in automation for all enabled games.
    
    Args:
        session_data: Session data for authentication
    """
    # Load check-in configuration
    checkin_config = CheckinConfig.from_env()
    
    results = run_daily_checkins(checkin_config, session_data)
    
    if results:
        # Display summary table
        table = create_summary_table(results)
        console.print("\n")
        console.print(table)
        
        # Display final summary
        successful_count, total_count = calculate_success_summary(results)
        display_final_summary(successful_count, total_count)
    else:
        console.print("⚠️  No games enabled for check-in", style="yellow")