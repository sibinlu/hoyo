#!/usr/bin/env python3
"""
HoyoLab Check-in Automation
Entry point for the application.
"""

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import sys

from login import check_login_status
from gi_checkin import perform_gi_checkin
from hsr_checkin import perform_hsr_checkin
from zzz_checkin import perform_zzz_checkin

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
        
        # Perform daily check-ins
        console.print("\n📅 Starting daily check-ins...", style="cyan")
        
        # Collect results for summary table
        results = []
        
        # Genshin Impact check-in
        console.print("\n🎮 Genshin Impact Check-in")
        gi_result = perform_gi_checkin()
        results.append(("🎮 Genshin Impact", gi_result))
        
        # Honkai Star Rail check-in
        console.print("\n🚀 Honkai Star Rail Check-in")
        hsr_result = perform_hsr_checkin()
        results.append(("🚀 Honkai Star Rail", hsr_result))
        
        # Zenless Zone Zero check-in
        console.print("\n⚡ Zenless Zone Zero Check-in")
        zzz_result = perform_zzz_checkin()
        results.append(("⚡ Zenless Zone Zero", zzz_result))
        
        # Create and display summary table
        table = Table(title="📊 Daily Check-in Summary", show_header=True, header_style="bold magenta")
        table.add_column("Game", style="bold", width=20)
        table.add_column("Status", justify="center", width=15)
        table.add_column("Message", width=30)
        
        total_success = 0
        for game, result in results:
            if result == "success":
                total_success += 1
                table.add_row(game, "[green]✅ Success[/green]", "[green]Check-in completed[/green]")
            elif result == "already_checked_in":
                total_success += 1
                table.add_row(game, "[cyan]ℹ️ Already Done[/cyan]", "[cyan]Already checked in[/cyan]")
            else:  # failed
                table.add_row(game, "[red]❌ Failed[/red]", "[red]Check-in failed[/red]")
        
        console.print("\n")
        console.print(table)
        
        # Overall summary
        if total_success == 3:
            console.print("\n🎉 All check-ins completed successfully!", style="bold green")
        elif total_success > 0:
            console.print(f"\n⚠️  {total_success}/3 check-ins completed", style="bold yellow")
        else:
            console.print("\n💥 All check-ins failed", style="bold red")
        
    except KeyboardInterrupt:
        console.print("\n⚠️  Operation cancelled by user", style="yellow")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

if __name__ == "__main__":
    main()