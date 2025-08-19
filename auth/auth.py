"""
HoyoLab login management
Handles authentication and session persistence for HoyoLab using secure session management.
"""

from playwright.sync_api import sync_playwright
from loguru import logger
from rich.console import Console

from .secure_session import get_session_manager

console = Console()

HOYOLAB_LOGIN_CHECK_URL = "https://www.hoyolab.com/setting/privacy"

def load_session():
    """Load saved session data using secure session manager."""
    session_manager = get_session_manager()
    return session_manager.load_session()

def save_session(cookies, local_storage=None):
    """Save session data using secure session manager."""
    session_manager = get_session_manager()
    return session_manager.save_session(cookies, local_storage)

def is_logged_in(page):
    """Check if user is logged in by checking privacy settings page."""
    try:
        page.goto(HOYOLAB_LOGIN_CHECK_URL)
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Check if we're on the privacy settings page (logged in)
        if "setting/privacy" in page.url:
            # Look for "Personal Information Settings" text
            if page.locator("text='Personal Information Settings'").count() > 0:
                logger.info("User is logged in - found Personal Information Settings")
                return True
        
        # If we're redirected or don't see the settings, user is not logged in
        logger.info(f"User not logged in - current URL: {page.url}")
        return False
        
    except Exception as e:
        logger.warning(f"Error checking login status: {e}")
        return False

def wait_for_login_and_close():
    """Open browser for user login, wait for them to close it, then save session."""
    console.print("🔑 Please log in to HoyoLab and close the browser window when done", style="yellow")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.goto(HOYOLAB_LOGIN_CHECK_URL)
            
            # Wait for user to close the browser
            try:
                # This will block until browser is closed
                page.wait_for_event("close", timeout=300000)  # 5 minutes timeout
            except:
                pass
            
            # Save cookies before browser closes
            try:
                cookies = context.cookies()
                if cookies:
                    if save_session(cookies):
                        console.print("✅ Session saved successfully", style="green")
                        return True
                    else:
                        console.print("⚠️ Failed to save session", style="yellow")
                        return False
            except Exception as e:
                logger.warning(f"Failed to save session: {e}")
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
        finally:
            try:
                browser.close()
            except:
                pass
    
    return False

def check_login_status():
    """Check if user is logged in, open browser for login if needed."""
    # First try headless check with saved session
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # Load saved session if available
        session_data = load_session()
        if session_data and session_data.get("cookies"):
            try:
                context.add_cookies(session_data["cookies"])
                logger.info(f"Loaded {len(session_data['cookies'])} cookies from session")
                
                page = context.new_page()
                
                if is_logged_in(page):
                    logger.info("User already logged in (headless check)")
                    browser.close()
                    return True
                    
            except Exception as e:
                logger.warning(f"Headless login check failed: {e}")
        
        browser.close()
    
    # If headless check fails, open visible browser for login
    logger.info("User not logged in, opening browser for authentication")
    return wait_for_login_and_close()