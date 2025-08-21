"""
Redeem functions for HoYoverse games
"""

from playwright.sync_api import sync_playwright
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from redeem.search import search_recent_codes, display_search_results

def redeem_zzz(session_data: dict, code: str) -> dict:
    redemption_url = f"https://zenless.hoyoverse.com/redemption?code={code}"
    steps = [
        (".web-cdkey-form__select--toggle", "region selector toggle", 100),
        (".web-cdkey-form__select--option:has-text('America')", "America region", 1000),
        ('button[type="submit"].web-cdkey-form__submit.title-font:has-text("Redeem")', "redeem button", 2000)
    ]
    msg_locator = "p.state-msg"
    return redeem(session_data, code, redemption_url, steps, msg_locator)

def redeem_hsr(session_data: dict, code: str) -> dict:
    redemption_url = f"https://hsr.hoyoverse.com/gift?code={code}"
    steps = [
        (".web-cdkey-form__select--toggle", "region selector toggle", 100),
        (".web-cdkey-form__select--option:has-text('America')", "America region", 1000),
        ('button[type="submit"].web-cdkey-form__submit:has-text("Redeem")', "redeem button", 2000)
    ]
    msg_locator = "div.tip-text"
    return redeem(session_data, code, redemption_url, steps, msg_locator)

def redeem_gi(session_data: dict, code: str) -> dict:
    redemption_url = f"https://genshin.hoyoverse.com/en/gift?code={code}"
    steps = [
        (".cdkey-select__btn", "region selector toggle", 100),
        (".cdkey-select__option:has-text('America')", "America region", 1000),
        ('button[type="submit"].cdkey-form__submit:has-text("Redeem")', "redeem button", 1000)
    ]
    msg_locator = ".cdkey-result__message"
    return redeem(session_data, code, redemption_url, steps, msg_locator)

def redeem(session_data: dict, code: str ,redemption_url: str, steps: list[tuple[str, str, int]], msg_locator: str) -> dict:
    """
    Redeem a code for Zenless Zone Zero.
    
    Args:
        session_data: Dictionary containing session/cookie data
        code: Redemption code to use
        
    Returns:
        dict: Result of the redemption attempt
    """
    console = Console()
    result = {"success": False, "message": ""}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        try:
            if session_data and 'cookies' in session_data:
                context.add_cookies(session_data['cookies'])
            
            page = context.new_page()
            logger.info(f"Navigating to: {redemption_url}")
            page.goto(redemption_url)
            page.wait_for_load_state('networkidle')
            
            
            for selector, description, timeout in steps:
                try:
                    element = page.locator(selector)
                    element.click()
                    logger.info(f"Clicked {description}")
                    page.wait_for_timeout(timeout)
                except Exception as e:
                    logger.error(f"Failed to click {description}: {e}")
                    result["message"] = f"Failed to click {description}"
                    return result
            
            # Check success mask and extract message
            for attempt in range(5): 
                message = page.locator(msg_locator)
                message.wait_for(state="attached", timeout=2000)
            
                if message.count() > 0:
                    result["success"] = True
                    result["message"] = message.text_content().strip() or ""
                    console.print(f"✅ {result['message']}", style="green")
                    break;
                elif attempt < 4:
                    page.wait_for_timeout(500)
                else:
                    result["message"] = "Redemption status unclear"
                    console.print("⚠️ Redemption status unclear", style="yellow")
                    
            # success_mask = page.locator("div.custom-mihoyo-common-mask[style*='rgba(0, 0, 0, 0.6)']")
            # if success_mask.count() > 0:
            #     logger.info("Success mask detected")
            #     result["success"] = True
            #     result["message"] = success_mask.locator(msg_locator).text_content() or ""
            #     result["message"] = result["message"].strip()
            #     console.print(f"✅ {result['message']}", style="green")
            # else:
            #     result["message"] = "Redemption status unclear"
            #     console.print("⚠️ Redemption status unclear", style="yellow")
                
        except Exception as e:
            logger.error(f"Error during redemption: {e}")
            result["message"] = f"Redemption failed: {str(e)}"
            console.print(f"❌ Redemption failed: {str(e)}", style="red")
        finally:
            browser.close()
    
    return result