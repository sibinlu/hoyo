"""
Main redeem orchestration module
Handles searching and displaying redeem codes from HoYoLab articles
"""

import json
import os
import time
from typing import Dict, List, Tuple
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from loguru import logger

from redeem.search import search_recent_codes, display_search_results
from redeem.redeem import redeem_zzz, redeem_hsr, redeem_gi

# Constants
REDEEMED_CODES_FILE = "redeemed_codes.json"
GAME_MAPPINGS = {
    "Zenless Zone Zero": ("ZZZ", redeem_zzz),
    "Honkai Star Rail": ("HSR", redeem_hsr),
    "Genshin Impact": ("GI", redeem_gi),
}


def load_redeemed_codes() -> Dict:
    """Load previously redeemed codes from local file."""
    if not os.path.exists(REDEEMED_CODES_FILE):
        return {}
    
    try:
        with open(REDEEMED_CODES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load redeemed codes: {e}")
        return {}


def save_redeemed_codes(redeemed_codes: Dict):
    """Save redeemed codes to local file."""
    try:
        with open(REDEEMED_CODES_FILE, 'w') as f:
            json.dump(redeemed_codes, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save redeemed codes: {e}")


def is_code_redeemed(redeemed_codes: Dict, game_key: str, code: str) -> bool:
    """Check if a code has been redeemed before for a specific game."""
    return game_key in redeemed_codes and code in redeemed_codes[game_key]


def mark_code_redeemed(redeemed_codes: Dict, game_key: str, code: str, message: str):
    """Mark a code as redeemed for a specific game."""
    if game_key not in redeemed_codes:
        redeemed_codes[game_key] = {}
    
    redeemed_codes[game_key][code] = {
        "message": message,
        "timestamp": datetime.now().isoformat()
    }


def create_summary_table(redemption_results: List[Tuple[str, str, str]]) -> Table:
    """Create a summary table of redemption results."""
    table = Table(title="🎁 Redemption Summary", show_header=True, header_style="bold magenta")
    table.add_column("Game", style="bold", width=20)
    table.add_column("Code", style="cyan", width=15)
    table.add_column("Result", width=40)
    
    for game, code, message in redemption_results:
        # Color coding based on result
        if "successfully" in message.lower():
            color = "green"
        elif "redeemed before" in message.lower():
            color = "yellow"
        elif "already in use" in message.lower():
            color = "orange3"
        else:
            color = "red"
        
        table.add_row(
            game,
            code,
            f"[{color}]{message}[/{color}]"
        )
    
    return table


def main_redeem(session_data: dict):
    """Main function to search for and automatically redeem codes from HoYoLab articles."""
    console = Console()
    console.print(Panel("🎁 HoYoLab Auto Redeem", style="bold blue"))
    
    # Load previously redeemed codes
    redeemed_codes = load_redeemed_codes()
    logger.info(f"Loaded {sum(len(codes) for codes in redeemed_codes.values())} previously redeemed codes")
    
    # Search for redeem codes from the last 7 days
    console.print("🔍 Searching for recent redeem codes...", style="cyan")
    search_results = search_recent_codes(session_data, 1)
    display_search_results(search_results)
    
    if not search_results:
        console.print("📭 No redeem codes found", style="yellow")
        return
    
    # Process each found code
    console.print("\n🎮 Processing redemption codes...", style="cyan")
    redemption_results = []
    
    for _, game_name, codes in search_results:
        if game_name not in GAME_MAPPINGS:
            logger.warning(f"Unknown game: {game_name}")
            continue
        
        game_key, redeem_func = GAME_MAPPINGS[game_name]
        
        for code in codes:
            # Check if already redeemed
            if is_code_redeemed(redeemed_codes, game_key, code):
                message = "Redeemed Before"
                logger.info(f"Skipping {game_key} code {code} - already redeemed")
            else:
                # Attempt redemption
                console.print(f"🎁 Redeeming {game_key} code: {code}", style="blue")
                try:
                    result = redeem_func(session_data, code)
                    message = result.get("message", "Unknown result")
                    
                    # Mark as redeemed if successful
                    if result.get("success", False):
                        mark_code_redeemed(redeemed_codes, game_key, code, message)
                        logger.info(f"Successfully redeemed {game_key} code {code}")
                    else:
                        logger.warning(f"Failed to redeem {game_key} code {code}: {message}")
                        
                except Exception as e:
                    message = f"Error: {str(e)}"
                    logger.error(f"Exception redeeming {game_key} code {code}: {e}")
            
            redemption_results.append((game_key, code, message))
            
            # Wait 2 seconds between redemptions
            time.sleep(2)
    
    # Save updated redeemed codes
    save_redeemed_codes(redeemed_codes)
    
    # Display summary table
    if redemption_results:
        console.print("\n")
        table = create_summary_table(redemption_results)
        console.print(table)
        
        # Statistics
        successful = sum(1 for _, _, msg in redemption_results if "successfully" in msg.lower())
        already_redeemed = sum(1 for _, _, msg in redemption_results if "redeemed before" in msg.lower())
        failed = len(redemption_results) - successful - already_redeemed
        
        console.print(f"\n📊 Summary: {successful} successful, {already_redeemed} already redeemed, {failed} failed", 
                     style="bold cyan")
    else:
        console.print("⚠️ No codes processed", style="yellow")