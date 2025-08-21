"""
Genshin Impact check-in implementation
Uses the BaseCheckin class to minimize code duplication.
"""

from playwright.sync_api import Page
from loguru import logger

from checkin.base_checkin import BaseCheckin
from checkin.config import GAMES, Game, CheckinConfig
from checkin.exceptions import CheckinResult

class GenshinImpactCheckin(BaseCheckin):
    """Genshin Impact specific check-in implementation."""
    
    def __init__(self, checkin_config: CheckinConfig = None, session_data: dict = None):
        super().__init__(checkin_config, session_data)
        self.config = GAMES[Game.GI]
    
    def _find_clickable_item(self, page: Page):
        """Find clickable check-in items (items with red point indicator)."""
        clickable_items = page.locator(self.config.clickable_selector)
        
        if clickable_items.count() > 0:
            logger.info(f"Found {clickable_items.count()} potential clickable items")
            return clickable_items.first
        
        logger.info("No clickable items found with red point indicator")
        return None
    
    def _get_javascript_click_selector(self) -> str:
        """Get selector for JavaScript fallback click."""
        return ".components-home-assets-__sign-content-test_---red-point---2jUBf9"
    
    def _handle_no_clickable_items(self, page: Page) -> CheckinResult:
        """
        Handle GI-specific logic when no clickable items are found.
        Check if all items are already signed.
        """
        # Check if all items are already signed (have has-signed class)
        all_items = page.locator(".components-home-assets-__sign-content-test_---sign-item---3gtMqV")
        signed_items = page.locator(".components-home-assets-__sign-content-test_---sign-item---3gtMqV.components-home-assets-__sign-content-test_---has-signed---1--Ffl")
        
        total_items = all_items.count()
        signed_count = signed_items.count()
        
        logger.info(f"GI check-in status: {signed_count}/{total_items} items signed")
        
        if total_items > 0 and signed_count == total_items:
            logger.info("All GI check-in items already completed")
        else:
            logger.info("No clickable GI check-in items - likely already completed")
        
        self.console.print("ℹ️  Already checked in today!", style="cyan")
        return CheckinResult.ALREADY_CHECKED_IN

# Factory function for backward compatibility
def perform_gi_checkin() -> str:
    """
    Perform Genshin Impact daily check-in.
    
    Returns:
        String result for backward compatibility ("success", "already_checked_in", "failed")
    """
    checkin = GenshinImpactCheckin()
    result = checkin.perform_checkin()
    return result.value