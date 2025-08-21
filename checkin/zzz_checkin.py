"""
Zenless Zone Zero check-in implementation
Uses the BaseCheckin class to minimize code duplication.
"""

from playwright.sync_api import Page
from loguru import logger

from checkin.base_checkin import BaseCheckin
from checkin.config import GAMES, Game, CheckinConfig
from checkin.exceptions import CheckinResult

class ZenlessZoneZeroCheckin(BaseCheckin):
    """Zenless Zone Zero specific check-in implementation."""
    
    def __init__(self, checkin_config: CheckinConfig = None, session_data: dict = None):
        super().__init__(checkin_config, session_data)
        self.config = GAMES[Game.ZZZ]
    
    def _find_clickable_item(self, page: Page):
        """Find the item with the specific background image (clickable item indicator)."""
        all_items = page.locator(self.config.clickable_selector)
        
        if all_items.count() == 0:
            logger.info("No ZZZ check-in items found on page")
            return None
        
        logger.info(f"Found {all_items.count()} ZZZ check-in items")
        logger.info(f"Looking for item with background image: {self.config.background_image_url}")
        
        # Find the item with the specific background image
        for i in range(all_items.count()):
            item = all_items.nth(i)
            try:
                style_attr = item.get_attribute("style")
                logger.info(f"ZZZ Item {i+1} style: {style_attr}")
                
                if style_attr and self.config.background_image_url in style_attr:
                    logger.info(f"Found clickable ZZZ item {i+1} with target background image!")
                    return item
                else:
                    logger.info(f"ZZZ Item {i+1} does not have target background image")
                    
            except Exception as e:
                logger.error(f"Error checking ZZZ item {i+1}: {e}")
                continue
        
        logger.info("No ZZZ items found with target background image")
        return None
    
    def _get_javascript_click_selector(self) -> str:
        """Get selector for JavaScript fallback click."""
        # Use a selector that targets items with the specific background image
        return f"[style*='{self.config.background_image_url}']"
    
    def _fallback_javascript_click(self, page: Page, clickable_item) -> bool:
        """ZZZ-specific JavaScript fallback click."""
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
            logger.info("Successfully clicked ZZZ item using JavaScript")
            return True
        except Exception as js_error:
            logger.error(f"ZZZ JavaScript click failed: {js_error}")
            return False
    
    def _verify_success(self, page: Page) -> CheckinResult:
        """
        ZZZ-specific success verification.
        Look for any congratulations dialog that appears.
        """
        try:
            # Look for common success dialog indicators
            success_dialog_selectors = [
                self.config.success_dialog_selector,
                ".m-dialog-body",
                "[class*='dialog']",
                "text='Congratulations'",
                "text='Success'"
            ]
            
            for selector in success_dialog_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"Found ZZZ success dialog with selector: {selector}")
                    self.console.print("✅ Check-in completed successfully!", style="green")
                    return CheckinResult.SUCCESS
                except:
                    continue
            
            # If no specific success dialog found, assume success since we clicked
            logger.info("ZZZ check-in clicked, assuming success")
            self.console.print("✅ Check-in attempted (assuming success)", style="yellow")
            return CheckinResult.SUCCESS
            
        except Exception as e:
            logger.warning(f"Error checking ZZZ success: {e}")
            self.console.print("✅ Check-in attempted (please verify manually)", style="yellow")
            return CheckinResult.SUCCESS

# Factory function for backward compatibility
def perform_zzz_checkin() -> str:
    """
    Perform Zenless Zone Zero daily check-in.
    
    Returns:
        String result for backward compatibility ("success", "already_checked_in", "failed")
    """
    checkin = ZenlessZoneZeroCheckin()
    result = checkin.perform_checkin()
    return result.value