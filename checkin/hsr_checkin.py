"""
Honkai Star Rail daily check-in automation
Handles automatic daily check-in for HSR rewards.
"""

from playwright.sync_api import sync_playwright
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from login import load_session

console = Console()

HSR_CHECKIN_URL = "https://act.hoyolab.com/bbs/event/signin/hkrpg/e202303301540311.html?act_id=e202303301540311&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_source=hoyolab&utm_medium=tools&utm_campaign=checkin&utm_id=6&lang=en-us&bbs_theme=light&bbs_theme_device=1"

def perform_hsr_checkin():
    """Perform Honkai Star Rail daily check-in."""
    console.print(Panel("🚀 Honkai Star Rail Daily Check-in", style="bold purple"))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # Load saved session
        session_data = load_session()
        if session_data and session_data.get("cookies"):
            try:
                context.add_cookies(session_data["cookies"])
                logger.info("Loaded session for HSR check-in")
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
            logger.info("Opening HSR check-in page...")
            page.goto(HSR_CHECKIN_URL)
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # Wait for the check-in items to load
            page.wait_for_timeout(3000)
            
            # Close any popup dialogs (app download dialog)
            try:
                close_button = page.locator(".components-pc-assets-__dialog_---dialog-close---3G9gO2")
                if close_button.count() > 0:
                    close_button.click()
                    logger.info("Closed popup dialog")
                    page.wait_for_timeout(1000)
            except Exception as e:
                logger.info(f"No dialog to close or failed to close: {e}")
            
            # Wait for all dialogs to disappear completely
            try:
                page.wait_for_selector(".m-dialog-wrapper", state="hidden", timeout=5000)
                logger.info("All dialogs have disappeared")
            except:
                logger.info("Dialog still present or timeout, continuing anyway")
            
            # Additional wait to ensure page is ready
            page.wait_for_timeout(2000)
            
            # Look for clickable check-in items
            all_items = page.locator(".components-pc-assets-__prize-list_---item---F852VZ")
            
            logger.info(f"Looking for items with selector: .components-pc-assets-__prize-list_---item---F852VZ")
            logger.info(f"Found {all_items.count()} total items")
            
            if all_items.count() > 0:
                logger.info(f"Found {all_items.count()} check-in items")
                
                # Find the item with the specific background image (clickable item indicator)
                clickable_item = None
                target_bg_image = "https://upload-static.hoyoverse.com/event/2023/04/21/5ccbbab8f5eb147df704e16f31fc5788_6285576485616685271.png"
                
                logger.info(f"Looking for item with background image: {target_bg_image}")
                
                for i in range(all_items.count()):
                    item = all_items.nth(i)
                    try:
                        # Get the style attribute to check background image
                        style_attr = item.get_attribute("style")
                        logger.info(f"Item {i+1} style: {style_attr}")
                        
                        if style_attr and target_bg_image in style_attr:
                            logger.info(f"Found clickable item {i+1} with target background image!")
                            clickable_item = item
                            break
                        else:
                            logger.info(f"Item {i+1} does not have target background image")
                            
                    except Exception as e:
                        logger.error(f"Error checking item {i+1}: {e}")
                        continue
                
                logger.info(f"Final clickable_item result: {'Found' if clickable_item else 'None'}")
                
                if clickable_item:
                    logger.info("Found clickable check-in item")
                    console.print("🎯 Found today's check-in reward!", style="green")
                    
                    try:
                        # Scroll to element and wait for it to be visible
                        clickable_item.scroll_into_view_if_needed()
                        page.wait_for_timeout(1000)
                        
                        # Move mouse to the element first to show where we're going to click
                        clickable_item.hover()
                        logger.info("Moved mouse to clickable item")
                        page.wait_for_timeout(2000)  # Wait so user can see where mouse is
                        
                        # Try clicking with force if needed
                        clickable_item.click(timeout=10000, force=True)
                        page.wait_for_timeout(3000)
                        
                        logger.info("Successfully clicked check-in item")
                        
                    except Exception as click_error:
                        logger.warning(f"Click failed, trying alternative method: {click_error}")
                        # Try clicking with JavaScript as fallback
                        try:
                            page.evaluate("document.querySelector('.components-pc-assets-__prize-list_---item---F852VZ').click()")
                            page.wait_for_timeout(3000)
                            logger.info("Successfully clicked using JavaScript")
                        except Exception as js_error:
                            logger.error(f"Both click methods failed: {js_error}")
                            browser.close()
                            return False
                    
                    # Check if check-in was successful by looking for the specific success message
                    success_message = "Congratulations Trailblazer! You've successfully checked in today!"
                    success_selector = f"text='{success_message}'"
                    
                    # Wait for success dialog to appear
                    try:
                        page.wait_for_selector(success_selector, timeout=10000)
                        success = True
                        logger.info("Found HSR success message")
                    except:
                        # Also check for the specific dialog title class
                        success_dialog = page.locator(".components-pc-assets-__dialog_---title---IfpJqm")
                        if success_dialog.count() > 0 and success_message in success_dialog.text_content():
                            success = True
                            logger.info("Found HSR success dialog")
                        else:
                            success = False
                            logger.warning("HSR success confirmation not found")
                    
                    if success:
                        console.print("✅ Check-in completed successfully!", style="green")
                        logger.info("HSR daily check-in successful")
                        browser.close()
                        return "success"
                    else:
                        console.print("✅ Check-in attempted (please verify manually)", style="yellow")
                        logger.info("HSR check-in clicked, but success confirmation unclear")
                        browser.close()
                        return "success"  # Assume success if clicked
                
                else:
                    # No clickable items found - likely already checked in
                    console.print("ℹ️  Already checked in today!", style="cyan")
                    logger.info("No clickable HSR check-in items - likely already completed")
                    
                    browser.close()
                    return "already_checked_in"
            
            else:
                logger.warning("No HSR check-in items found on page")
                console.print("⚠️  Could not find check-in items", style="yellow")
                browser.close()
                return "failed"
                
        except Exception as e:
            logger.error(f"Error during HSR check-in: {e}")
            console.print(f"❌ Check-in failed: {e}", style="red")
            browser.close()
            return "failed"

if __name__ == "__main__":
    perform_hsr_checkin()