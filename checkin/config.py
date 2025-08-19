"""
Configuration system for HoYoverse check-in automation
Centralizes all game-specific settings and application configuration.
"""

import os
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

class Game(Enum):
    GI = "gi"
    HSR = "hsr"
    ZZZ = "zzz"

@dataclass
class GameConfig:
    """Configuration for a specific game's check-in process."""
    name: str
    url: str
    console_style: str
    clickable_selector: str
    success_message: str
    popup_close_selector: str
    success_dialog_selector: str
    background_image_url: str = ""

@dataclass
class AppConfig:
    """Application-wide configuration settings."""
    session_timeout: int = 15000
    page_load_timeout: int = 15000
    click_timeout: int = 10000
    short_wait: int = 1000
    medium_wait: int = 3000
    success_wait_timeout: int = 10000
    dialog_close_timeout: int = 5000
    headless: bool = True
    max_retries: int = 3
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls(
            headless=os.getenv("HOYO_HEADLESS", "true").lower() == "true",
            max_retries=int(os.getenv("HOYO_MAX_RETRIES", "3")),
            session_timeout=int(os.getenv("HOYO_SESSION_TIMEOUT", "15000")),
        )

# Game-specific configurations
GAMES: Dict[Game, GameConfig] = {
    Game.GI: GameConfig(
        name="🎮 Genshin Impact",
        url="https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_source=hoyolab&utm_medium=tools&lang=en-us&bbs_theme=light&bbs_theme_device=1",
        console_style="bold blue",
        clickable_selector=".components-home-assets-__sign-content-test_---sign-item---3gtMqV:has(.components-home-assets-__sign-content-test_---red-point---2jUBf9)",
        success_message="Congratulations, Traveler! You checked in today.",
        success_dialog_selector=".components-common-common-dialog-__index_---title---xH8wpC",
        popup_close_selector=".components-home-assets-__sign-guide_---guide-close---2VvmzE",
    ),
    
    Game.HSR: GameConfig(
        name="🚀 Honkai Star Rail",
        url="https://act.hoyolab.com/bbs/event/signin/hkrpg/e202303301540311.html?act_id=e202303301540311&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_source=hoyolab&utm_medium=tools&utm_campaign=checkin&utm_id=6&lang=en-us&bbs_theme=light&bbs_theme_device=1",
        console_style="bold purple",
        clickable_selector=".components-pc-assets-__prize-list_---item---F852VZ",
        success_message="Congratulations Trailblazer! You've successfully checked in today!",
        success_dialog_selector=".components-pc-assets-__dialog_---title---IfpJqm",
        popup_close_selector=".components-pc-assets-__dialog_---dialog-close---3G9gO2",
        background_image_url="https://upload-static.hoyoverse.com/event/2023/04/21/5ccbbab8f5eb147df704e16f31fc5788_6285576485616685271.png",
    ),
    
    Game.ZZZ: GameConfig(
        name="⚡ Zenless Zone Zero",
        url="https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_campaign=checkin&utm_id=8&utm_medium=tools&utm_source=hoyolab&lang=en-us&bbs_theme=light&bbs_theme_device=1",
        console_style="bold yellow",
        clickable_selector=".components-pc-assets-__prize-list_---item---F852VZ",
        success_message="Congratulations! Check-in successful!",  # Update with actual message
        success_dialog_selector=".components-pc-assets-__dialog_---dialog-body---1SieDs",
        popup_close_selector=".components-pc-assets-__dialog_---dialog-close---3G9gO2",
        background_image_url="https://act-webstatic.hoyoverse.com/event-static/2024/06/17/3b211daae47bbfac6bed5b447374a325_3353871917298254056.png",
    ),
}

def get_enabled_games() -> List[Game]:
    """Get list of enabled games from environment or default to all."""
    env_games = os.getenv("HOYO_ENABLED_GAMES", "gi,hsr,zzz").split(",")
    enabled = []
    
    for game_str in env_games:
        try:
            enabled.append(Game(game_str.strip().lower()))
        except ValueError:
            continue
    
    return enabled or list(Game)