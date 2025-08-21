"""
HoYoLab redeem code search functionality.
Searches for redeem codes in official HoYoLab articles.
"""

import re
import difflib
from typing import List, Tuple, Dict
from playwright.sync_api import sync_playwright
from loguru import logger
from rich.console import Console
from dateutil import parser
from datetime import date

HSR = "Honkai Star Rail" 
GI = "Genshin Impact"
ZZZ = "Zenless Zone Zero"

console = Console()

def search_recent_codes(session_data: dict, days: int) -> List[Tuple[date, str, List[str]]]:
    """
    Search for redeem codes in HoYoLab articles within the specified number of days.
    
    Args:
        session_data: Session data for authentication
        days: Number of days to look back from today
        
    Returns:
        List of tuples containing (date, game, code_array) within the specified timeframe
    """
    from datetime import datetime, timedelta
    
    all_results = search(session_data)
    cutoff_date = datetime.now().date() - timedelta(days=days)
    
    # Filter results to only include articles within the specified days
    filtered_results = [
        (article_date, game, codes) 
        for article_date, game, codes in all_results 
        if article_date >= cutoff_date
    ]
    
    logger.info(f"Filtered {len(all_results)} results to {len(filtered_results)} within {days} days")
    return filtered_results

def search(session_data: dict) -> List[Tuple[date, str, List[str]]]:
    """
    Search for redeem codes in HoYoLab articles.
    
    Args:
        session_data: Session data for authentication
        
    Returns:
        List of tuples containing (date, game, code_array)
    """
    results = []
    url = "https://www.hoyolab.com/accountCenter/postList?id=129928383"
    
    logger.info("Starting redeem code search")
    console.print("🔍 Searching for redeem codes in HoYoLab articles...", style="cyan")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        try:
            # Setup session
            if session_data and session_data.get("cookies"):
                context.add_cookies(session_data["cookies"])
                logger.info("Session loaded for redeem code search")
            
            page = context.new_page()
            logger.info(f"Navigating to: {url}")
            page.goto(url)
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # Find all article cards
            article_cards = page.locator("div.mhy-article-card")
            card_count = article_cards.count()
            logger.info(f"Found {card_count} article cards")
            
            if card_count == 0:
                console.print("⚠️  No articles found", style="yellow")
                return results
            
            for i in range(card_count):
                try:
                    card = article_cards.nth(i)
                    
                    # Extract date and game from mhy-article-card__info
                    info_element = card.locator(".mhy-article-card__info")
                    if info_element.count() == 0:
                        continue
                        
                    info_text = info_element.inner_text().strip()
                    logger.debug(f"Article {i+1} info: {info_text}")
                    
                    # Parse date and game from format like "08/14 • Honkai: Star Rail"
                    if "•" not in info_text:
                        continue
                        
                    parts = info_text.split("•", 1)
                    if len(parts) != 2:
                        continue
                        
                    date = parser.parse(parts[0].strip(), fuzzy=True).date();
                    matches = difflib.get_close_matches(parts[1].strip(), [HSR, GI, ZZZ])
                    game = matches[0] if len(matches) > 0 else ""
                    
                    # Extract content from mhy-article-card__content
                    content_element = card.locator(".mhy-article-card__content")
                    if content_element.count() == 0:
                        continue
                        
                    content_text = content_element.inner_text().strip()
                    logger.debug(f"Article {i+1} content preview: {content_text[:100]}...")
                    
                    # Find redeem codes using regex: alphanumeric codes 5+ characters
                    code_pattern = r'(?<!\.)\b[0-9a-zA-Z]{5,}\b(?!\.)'
                    codes = re.findall(code_pattern, content_text)
                    
                    # Filter out common words/false positives
                    filtered_codes = []
                    for code in codes:
                        # Skip if it's all numbers (likely not a redeem code)
                        if code.isdigit():
                            continue
                        # Skip if it's all letters and looks like a common word
                        if code.isalpha() and len(code) < 8:
                            continue
                        filtered_codes.append(code)
                    
                    if filtered_codes:
                        results.append((date, game, filtered_codes))
                        logger.info(f"Found codes for {game} ({date}): {filtered_codes}")
                    
                except Exception as e:
                    logger.warning(f"Error processing article {i+1}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error during redeem code search: {e}")
            console.print(f"❌ Search failed: {e}", style="red")
        finally:
            browser.close()
    
    logger.info(f"Redeem code search completed. Found {len(results)} articles with codes")
    return results


def display_search_results(results: List[Tuple[str, str, List[str]]]):
    """
    Display search results in a formatted table.
    
    Args:
        results: List of (date, game, codes) tuples
    """
    if not results:
        console.print("📭 No redeem codes found in recent articles", style="yellow")
        return
    
    from rich.table import Table
    
    table = Table(title="🎁 Redeem Codes Found", show_header=True, header_style="bold magenta")
    table.add_column("Date", style="cyan", width=15)
    table.add_column("Game", style="blue", width=20)
    table.add_column("Codes", style="green")
    
    for date, game, codes in results:
        codes_str = ", ".join(codes) if codes else "None"
        table.add_row(date.strftime("%Y-%m-%d"), game, codes_str)
    
    console.print("\n")
    console.print(table)
    
    total_codes = sum(len(codes) for _, _, codes in results)
    console.print(f"\n🎉 Total: {total_codes} redeem codes found across {len(results)} articles", style="bold green")