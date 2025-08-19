"""
Exception handling and result types for HoYoverse check-in automation.
Provides structured error handling and result classification.
"""

from enum import Enum
from typing import Tuple, Optional

class CheckinResult(Enum):
    """Possible outcomes of a check-in attempt."""
    SUCCESS = "success"
    ALREADY_CHECKED_IN = "already_checked_in"
    FAILED = "failed"
    SESSION_EXPIRED = "session_expired"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"

class CheckinException(Exception):
    """Base exception for check-in operations."""
    
    def __init__(self, message: str, result: CheckinResult = CheckinResult.FAILED):
        super().__init__(message)
        self.result = result

class SessionExpiredException(CheckinException):
    """Raised when session is expired or invalid."""
    
    def __init__(self, message: str = "Session expired or invalid"):
        super().__init__(message, CheckinResult.SESSION_EXPIRED)

class NetworkException(CheckinException):
    """Raised when network-related errors occur."""
    
    def __init__(self, message: str = "Network error occurred"):
        super().__init__(message, CheckinResult.NETWORK_ERROR)

class TimeoutException(CheckinException):
    """Raised when operations timeout."""
    
    def __init__(self, message: str = "Operation timed out"):
        super().__init__(message, CheckinResult.TIMEOUT_ERROR)

def classify_error(exception: Exception) -> Tuple[CheckinResult, str]:
    """
    Classify an exception and return appropriate result and message.
    
    Args:
        exception: The exception to classify
        
    Returns:
        Tuple of (CheckinResult, error_message)
    """
    error_str = str(exception).lower()
    
    if isinstance(exception, CheckinException):
        return exception.result, str(exception)
    
    # Classify based on error message content
    if any(keyword in error_str for keyword in ["timeout", "timed out"]):
        return CheckinResult.TIMEOUT_ERROR, f"Operation timed out: {exception}"
    
    elif any(keyword in error_str for keyword in ["network", "connection", "dns"]):
        return CheckinResult.NETWORK_ERROR, f"Network error: {exception}"
    
    elif any(keyword in error_str for keyword in ["session", "login", "auth", "unauthorized"]):
        return CheckinResult.SESSION_EXPIRED, f"Session expired: {exception}"
    
    else:
        return CheckinResult.FAILED, f"Unexpected error: {exception}"

def get_result_display_info(result: CheckinResult) -> Tuple[str, str, str]:
    """
    Get display information for a result.
    
    Args:
        result: The CheckinResult to get info for
        
    Returns:
        Tuple of (status_text, message, color_style)
    """
    display_map = {
        CheckinResult.SUCCESS: ("✅ Success", "Check-in completed", "green"),
        CheckinResult.ALREADY_CHECKED_IN: ("ℹ️ Already Done", "Already checked in", "cyan"),
        CheckinResult.FAILED: ("❌ Failed", "Check-in failed", "red"),
        CheckinResult.SESSION_EXPIRED: ("🔑 Session Expired", "Please login again", "yellow"),
        CheckinResult.NETWORK_ERROR: ("🌐 Network Error", "Connection failed", "red"),
        CheckinResult.TIMEOUT_ERROR: ("⏱️ Timeout", "Operation timed out", "yellow"),
    }
    
    return display_map.get(result, ("❓ Unknown", "Unknown status", "white"))