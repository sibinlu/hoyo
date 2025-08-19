"""
Honkai Star Rail check-in implementation
Uses the BaseCheckin class to minimize code duplication.
"""

from playwright.sync_api import Page
from loguru import logger

from checkin.base_checkin import BaseCheckin
from checkin.config import GAMES, Game, AppConfig
from checkin.exceptions import CheckinResult

class HonkaiStarRailCheckin(BaseCheckin):
    """Honkai Star Rail specific check-in implementation."""
    
    def __init__(self, app_config: AppConfig = None, session_data: dict = None):
        super().__init__(app_config, session_data)
        self.config = GAMES[Game.HSR]
    
    def _find_clickable_item(self, page: Page):
        """Find the item with the specific background image (clickable item indicator)."""
        all_items = page.locator(self.config.clickable_selector)
        
        if all_items.count() == 0:
            logger.info("No HSR check-in items found on page")
            return None
        
        logger.info(f"Found {all_items.count()} HSR check-in items")
        logger.info(f"Looking for item with background image: {self.config.background_image_url}")
        
        # Find the item with the specific background image
        for i in range(all_items.count()):
            item = all_items.nth(i)
            try:
                style_attr = item.get_attribute("style")
                logger.info(f"HSR Item {i+1} style: {style_attr}")
                
                if style_attr and self.config.background_image_url in style_attr:
                    logger.info(f"Found clickable HSR item {i+1} with target background image!")
                    return item
                else:
                    logger.info(f"HSR Item {i+1} does not have target background image")
                    
            except Exception as e:
                logger.error(f"Error checking HSR item {i+1}: {e}")
                continue
        
        logger.info("No HSR items found with target background image")
        return None
    
    def _get_javascript_click_selector(self) -> str:
        """Get selector for JavaScript fallback click."""
        # Use a selector that targets items with the specific background image
        return f"[style*='{self.config.background_image_url}']"
    
    def _fallback_javascript_click(self, page: Page, clickable_item) -> bool:
        """HSR-specific JavaScript fallback click."""
        try:
            js_code = f"""
            const items = document.querySelectorAll('{self.config.clickable_selector}');
            for (let item of items) {{
                if (item.style.backgroundImage && item.style.backgroundImage.includes('{self.config.background_image_url}')) {{
                    item.click();
                    break;
                }}
            }}
            """
            page.evaluate(js_code)
            page.wait_for_timeout(self.app_config.medium_wait)
            logger.info("Successfully clicked HSR item using JavaScript")
            return True
        except Exception as js_error:
            logger.error(f"HSR JavaScript click failed: {js_error}")
            return False

# Factory function for backward compatibility
def perform_hsr_checkin() -> str:
    """
    Perform Honkai Star Rail daily check-in.
    
    Returns:
        String result for backward compatibility ("success", "already_checked_in", "failed")
    """
    checkin = HonkaiStarRailCheckin()
    result = checkin.perform_checkin()
    return result.value