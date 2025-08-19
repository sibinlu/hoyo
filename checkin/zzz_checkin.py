"""
Zenless Zone Zero daily check-in automation
Handles automatic daily check-in for ZZZ rewards.
"""

from playwright.sync_api import sync_playwright
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from login import load_session

console = Console()

ZZZ_CHECKIN_URL = "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_campaign=checkin&utm_id=8&utm_medium=tools&utm_source=hoyolab&lang=en-us&bbs_theme=light&bbs_theme_device=1"

def perform_zzz_checkin():
    """Perform Zenless Zone Zero daily check-in."""
    console.print(Panel("⚡ Zenless Zone Zero Daily Check-in", style="bold yellow"))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # Load saved session
        session_data = load_session()
        if session_data and session_data.get("cookies"):
            try:
                context.add_cookies(session_data["cookies"])
                logger.info("Loaded session for ZZZ check-in")
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
            logger.info("Opening ZZZ check-in page...")
            page.goto(ZZZ_CHECKIN_URL)
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
                target_bg_image = "https://act-webstatic.hoyoverse.com/event-static/2024/06/17/3b211daae47bbfac6bed5b447374a325_3353871917298254056.png"
                
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
                            page.evaluate(f"document.querySelector('[style*=\"{target_bg_image}\"]').click()")
                            page.wait_for_timeout(3000)
                            logger.info("Successfully clicked using JavaScript")
                        except Exception as js_error:
                            logger.error(f"Both click methods failed: {js_error}")
                            browser.close()
                            return False
                    
                    # Check if check-in was successful by looking for congratulations dialog
                    # Wait for any congratulations dialog to appear
                    try:
                        # Look for common success dialog indicators
                        success_dialog_selectors = [
                            ".components-pc-assets-__dialog_---dialog-body---1SieDs",
                            ".m-dialog-body",
                            "[class*='dialog']",
                            "text='Congratulations'",
                            "text='Success'"
                        ]
                        
                        success = False
                        for selector in success_dialog_selectors:
                            try:
                                page.wait_for_selector(selector, timeout=5000)
                                success = True
                                logger.info(f"Found success dialog with selector: {selector}")
                                break
                            except:
                                continue
                        
                        if success:
                            console.print("✅ Check-in completed successfully!", style="green")
                            logger.info("ZZZ daily check-in successful")
                            browser.close()
                            return "success"
                        else:
                            console.print("✅ Check-in attempted (please verify manually)", style="yellow")
                            logger.info("ZZZ check-in clicked, but success confirmation unclear")
                            browser.close()
                            return "success"  # Assume success if clicked
                        
                    except Exception as success_check_error:
                        logger.warning(f"Error checking success: {success_check_error}")
                        console.print("✅ Check-in attempted (please verify manually)", style="yellow")
                        browser.close()
                        return "success"  # Assume success if clicked
                
                else:
                    # No clickable items found - likely already checked in
                    console.print("ℹ️  Already checked in today!", style="cyan")
                    logger.info("No clickable ZZZ check-in items - likely already completed")
                    
                    browser.close()
                    return "already_checked_in"
            
            else:
                logger.warning("No ZZZ check-in items found on page")
                console.print("⚠️  Could not find check-in items", style="yellow")
                browser.close()
                return "failed"
                
        except Exception as e:
            logger.error(f"Error during ZZZ check-in: {e}")
            console.print(f"❌ Check-in failed: {e}", style="red")
            browser.close()
            return "failed"

if __name__ == "__main__":
    perform_zzz_checkin()