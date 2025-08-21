"""
Base check-in class for HoYoverse games
Eliminates code duplication by providing shared functionality.
"""

from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, Page
from loguru import logger
from rich.console import Console

from checkin.config import GameConfig, CheckinConfig
from checkin.exceptions import CheckinResult, CheckinException, SessionExpiredException, TimeoutException, classify_error

class BaseCheckin(ABC):
    """Base class for game check-in automation."""
    
    def __init__(self, checkin_config: CheckinConfig = None, session_data: dict = None):
        self.checkin_config = checkin_config or CheckinConfig()
        self.console = Console()
        self.session_data = session_data
    
    def perform_checkin(self) -> CheckinResult:
        """
        Main check-in flow that orchestrates the entire process.
        
        Returns:
            CheckinResult indicating the outcome of the check-in attempt
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.checkin_config.headless)
            context = browser.new_context()
            
            try:
                # Setup session
                if not self._setup_session(context):
                    return CheckinResult.SESSION_EXPIRED
                
                page = context.new_page()
                return self._execute_checkin_flow(page)
                
            except Exception as e:
                result, message = classify_error(e)
                logger.error(f"Error during {self.config.name} check-in: {message}")
                self.console.print(f"❌ Check-in failed: {message}", style="red")
                return result
            finally:
                browser.close()
    
    def _setup_session(self, context) -> bool:
        """
        Setup browser context with saved session data.
        
        Args:
            context: Browser context to setup
            
        Returns:
            True if session setup successful, False otherwise
        """
        if not self.session_data or not self.session_data.get("cookies"):
            logger.error("No valid session found. Please login first.")
            self.console.print("❌ No valid session found. Please login first.", style="red")
            return False
        
        try:
            context.add_cookies(self.session_data["cookies"])
            logger.info(f"Loaded session for {self.config.name} check-in")
            return True
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            self.console.print(f"❌ Failed to load session: {e}", style="red")
            return False
    
    def _execute_checkin_flow(self, page: Page) -> CheckinResult:
        """
        Execute the main check-in flow.
        
        Args:
            page: Browser page to use
            
        Returns:
            CheckinResult indicating the outcome
        """
        # Navigate to check-in page
        logger.info(f"Opening {self.config.name} check-in page...")
        page.goto(self.config.url)
        page.wait_for_load_state("networkidle", timeout=self.checkin_config.page_load_timeout)
        
        # Close any popup dialogs
        self._close_popups(page)
        
        # Wait for page to be ready
        page.wait_for_timeout(self.checkin_config.medium_wait)
        
        # Find clickable items
        clickable_item = self._find_clickable_item(page)
        
        if not clickable_item:
            return self._handle_no_clickable_items(page)
        
        # Attempt to click the item
        if self._attempt_click(page, clickable_item):
            return self._verify_success(page)
        
        return CheckinResult.FAILED
    
    def _close_popups(self, page: Page):
        """Close any popup dialogs that might interfere with check-in."""
        try:
            close_button = page.locator(self.config.popup_close_selector)
            if close_button.count() > 0:
                close_button.click()
                logger.info(f"Closed popup dialog for {self.config.name}")
                page.wait_for_timeout(self.checkin_config.short_wait)
        except Exception as e:
            logger.info(f"No dialog to close for {self.config.name} or failed to close: {e}")
        
        # Wait for dialogs to disappear
        self._wait_for_dialogs_to_close(page)
    
    def _wait_for_dialogs_to_close(self, page: Page):
        """Wait for all dialogs to disappear completely."""
        dialog_containers = [".m-dialog-wrapper", ".custom-mihoyo-common-container"]
        
        for container in dialog_containers:
            try:
                page.wait_for_selector(container, state="hidden", timeout=self.checkin_config.dialog_close_timeout)
                logger.info(f"All dialogs have disappeared for {self.config.name}")
                break
            except:
                continue
        
        # Additional wait to ensure page stability
        page.wait_for_timeout(self.checkin_config.short_wait)
    
    @abstractmethod
    def _find_clickable_item(self, page: Page):
        """
        Find the clickable check-in item for this specific game.
        
        Args:
            page: Browser page to search
            
        Returns:
            Playwright locator for the clickable item, or None if not found
        """
        pass
    
    def _handle_no_clickable_items(self, page: Page) -> CheckinResult:
        """Handle the case when no clickable items are found."""
        logger.info(f"No clickable {self.config.name} check-in items - likely already completed")
        self.console.print("ℹ️  Already checked in today!", style="cyan")
        return CheckinResult.ALREADY_CHECKED_IN
    
    def _attempt_click(self, page: Page, clickable_item) -> bool:
        """
        Attempt to click the check-in item.
        
        Args:
            page: Browser page
            clickable_item: The item to click
            
        Returns:
            True if click was successful, False otherwise
        """
        try:
            logger.info(f"Found clickable {self.config.name} check-in item")
            self.console.print("🎯 Found today's check-in reward!", style="green")
            
            # Scroll to element and hover
            clickable_item.scroll_into_view_if_needed()
            page.wait_for_timeout(self.checkin_config.short_wait)
            clickable_item.hover()
            logger.info("Moved mouse to clickable item")
            page.wait_for_timeout(self.checkin_config.short_wait)
            
            # Try clicking
            clickable_item.click(timeout=self.checkin_config.click_timeout, force=True)
            page.wait_for_timeout(self.checkin_config.medium_wait)
            
            logger.info("Successfully clicked check-in item")
            return True
            
        except Exception as click_error:
            logger.warning(f"Click failed, trying JavaScript method: {click_error}")
            return self._fallback_javascript_click(page, clickable_item)
    
    def _fallback_javascript_click(self, page: Page, clickable_item) -> bool:
        """
        Fallback click method using JavaScript.
        
        Args:
            page: Browser page
            clickable_item: The item to click
            
        Returns:
            True if click was successful, False otherwise
        """
        try:
            # Get a more specific selector for JavaScript click
            js_selector = self._get_javascript_click_selector()
            if js_selector:
                page.evaluate(f"document.querySelector('{js_selector}').click()")
                page.wait_for_timeout(self.checkin_config.medium_wait)
                logger.info("Successfully clicked using JavaScript")
                return True
        except Exception as js_error:
            logger.error(f"Both click methods failed: {js_error}")
        
        return False
    
    @abstractmethod
    def _get_javascript_click_selector(self) -> str:
        """
        Get a CSS selector suitable for JavaScript clicking.
        
        Returns:
            CSS selector string for JavaScript click fallback
        """
        pass
    
    def _verify_success(self, page: Page) -> CheckinResult:
        """
        Verify that the check-in was successful by looking for success indicators.
        
        Args:
            page: Browser page to check
            
        Returns:
            CheckinResult indicating success or failure
        """
        try:
            # Wait for success dialog to appear
            success_selector = f"text='{self.config.success_message}'"
            page.wait_for_selector(success_selector, timeout=self.checkin_config.success_wait_timeout)
            logger.info(f"{self.config.name} success message found")
            self.console.print("✅ Check-in completed successfully!", style="green")
            return CheckinResult.SUCCESS
            
        except:
            # Fallback: check for success dialog element
            success_dialog = page.locator(self.config.success_dialog_selector)
            if success_dialog.count() > 0:
                dialog_text = success_dialog.text_content()
                if self.config.success_message in dialog_text:
                    logger.info(f"{self.config.name} success dialog found")
                    self.console.print("✅ Check-in completed successfully!", style="green")
                    return CheckinResult.SUCCESS
            
            # If we got here, assume success since we clicked
            logger.info(f"{self.config.name} check-in clicked, assuming success")
            self.console.print("✅ Check-in attempted (assuming success)", style="yellow")
            return CheckinResult.SUCCESS