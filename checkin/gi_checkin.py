"""
Genshin Impact daily check-in automation
Handles automatic daily check-in for Genshin Impact rewards.
"""

from playwright.sync_api import sync_playwright
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from login import load_session

console = Console()

GI_CHECKIN_URL = "https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_source=hoyolab&utm_medium=tools&lang=en-us&bbs_theme=light&bbs_theme_device=1"

def perform_gi_checkin():
    """Perform Genshin Impact daily check-in."""
    console.print(Panel("🎮 Genshin Impact Daily Check-in", style="bold blue"))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # Load saved session
        session_data = load_session()
        if session_data and session_data.get("cookies"):
            try:
                context.add_cookies(session_data["cookies"])
                logger.info("Loaded session for GI check-in")
            except Exception as e:
                logger.error(f"Failed to load session: {e}")
                browser.close()
                return False
        else:
            logger.error("No valid session found. Please login first.")
            browser.close()
            return False
        
        page = context.new_page()
        
        try:
            logger.info("Opening GI check-in page...")
            page.goto(GI_CHECKIN_URL)
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # Close any popup dialogs (app download guide)
            try:
                close_button = page.locator(".components-home-assets-__sign-guide_---guide-close---2VvmzE")
                if close_button.count() > 0:
                    close_button.click()
                    logger.info("Closed GI app download guide dialog")
                    page.wait_for_timeout(1000)
            except Exception as e:
                logger.info(f"No GI dialog to close or failed to close: {e}")
            
            # Wait for all dialogs to disappear completely
            try:
                page.wait_for_selector(".custom-mihoyo-common-container", state="hidden", timeout=5000)
                logger.info("All GI dialogs have disappeared")
            except:
                logger.info("GI dialog still present or timeout, continuing anyway")
            
            # Wait for the check-in items to load
            page.wait_for_timeout(3000)
            
            # Look for clickable check-in items (items with red point indicator)
            clickable_items = page.locator(".components-home-assets-__sign-content-test_---sign-item---3gtMqV:has(.components-home-assets-__sign-content-test_---red-point---2jUBf9)")
            
            if clickable_items.count() > 0:
                logger.info("Found clickable check-in item")
                console.print("🎯 Found today's check-in reward!", style="green")
                
                try:
                    # Scroll to element and wait for it to be visible
                    first_item = clickable_items.first
                    first_item.scroll_into_view_if_needed()
                    page.wait_for_timeout(1000)
                    
                    # Try clicking with force if needed
                    first_item.click(timeout=10000, force=True)
                    page.wait_for_timeout(3000)
                    
                    logger.info("Successfully clicked check-in item")
                    
                except Exception as click_error:
                    logger.warning(f"Click failed, trying alternative method: {click_error}")
                    # Try clicking with JavaScript as fallback
                    try:
                        page.evaluate("document.querySelector('.components-home-assets-__sign-content-test_---red-point---2jUBf9').closest('.components-home-assets-__sign-content-test_---sign-item---3gtMqV').click()")
                        page.wait_for_timeout(3000)
                        logger.info("Successfully clicked using JavaScript")
                    except Exception as js_error:
                        logger.error(f"Both click methods failed: {js_error}")
                        browser.close()
                        return False
                
                # Check if check-in was successful by looking for the specific success message
                success_message = "Congratulations, Traveler! You checked in today."
                success_selector = f"text='{success_message}'"
                
                # Wait for success dialog to appear
                try:
                    page.wait_for_selector(success_selector, timeout=10000)
                    success = True
                    logger.info("Found success message")
                except:
                    # Also check for the specific dialog class
                    success_dialog = page.locator(".components-common-common-dialog-__index_---title---xH8wpC")
                    if success_dialog.count() > 0 and success_message in success_dialog.text_content():
                        success = True
                        logger.info("Found success dialog")
                    else:
                        success = False
                        logger.warning("Success confirmation not found")
                
                if success:
                    console.print("✅ Check-in completed successfully!", style="green")
                    logger.info("GI daily check-in successful")
                    browser.close()
                    return "success"
                else:
                    console.print("✅ Check-in attempted (please verify manually)", style="yellow")
                    logger.info("GI check-in clicked, but success confirmation unclear")
                    browser.close()
                    return "success"  # Assume success if clicked
            
            else:
                # Check if all items are already signed (have has-signed class)
                all_items = page.locator(".components-home-assets-__sign-content-test_---sign-item---3gtMqV")
                signed_items = page.locator(".components-home-assets-__sign-content-test_---sign-item---3gtMqV.components-home-assets-__sign-content-test_---has-signed---1--Ffl")
                
                logger.info(f"Total items: {all_items.count()}, Signed items: {signed_items.count()}")
                
                if all_items.count() > 0 and signed_items.count() == all_items.count():
                    console.print("ℹ️  Already checked in today!", style="cyan")
                    logger.info("All GI check-in items already completed")
                else:
                    console.print("ℹ️  Already checked in today!", style="cyan")
                    logger.info("No clickable GI check-in items - likely already completed")
                
                browser.close()
                return "already_checked_in"
                
        except Exception as e:
            logger.error(f"Error during GI check-in: {e}")
            console.print(f"❌ Check-in failed: {e}", style="red")
            browser.close()
            return "failed"

if __name__ == "__main__":
    perform_gi_checkin()