"""
Secure session management for HoYoverse check-in automation.
Provides encrypted storage and secure handling of session data.
"""

import json
import os
import stat
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    logger.warning("cryptography package not available. Session data will not be encrypted.")
    CRYPTO_AVAILABLE = False

class SecureSessionManager:
    """
    Manages secure storage and retrieval of session data.
    Uses encryption if cryptography package is available.
    """
    
    def __init__(self, session_path: str = "checkin"):
        self.session_dir = Path(session_path)
        self.session_file = self.session_dir / "hoyo_session_data.json"
        self.key_file = self.session_dir / ".session_key"
        
        # Ensure session directory exists
        self.session_dir.mkdir(exist_ok=True)
        
        # Set restrictive permissions on directory
        try:
            os.chmod(self.session_dir, stat.S_IRWXU)  # 700 - owner only
        except OSError as e:
            logger.warning(f"Could not set directory permissions: {e}")
    
    def _get_or_create_key(self) -> bytes:
        """
        Get existing encryption key or create a new one.
        
        Returns:
            Encryption key as bytes
        """
        if not CRYPTO_AVAILABLE:
            return b"dummy_key"  # Placeholder when crypto not available
        
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                logger.debug("Loaded existing encryption key")
                return key
            except Exception as e:
                logger.warning(f"Failed to load existing key: {e}")
        
        # Create new key
        key = Fernet.generate_key()
        try:
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions on key file
            os.chmod(self.key_file, stat.S_IRUSR | stat.S_IWUSR)  # 600 - owner read/write only
            logger.info("Created new encryption key")
            return key
        except Exception as e:
            logger.error(f"Failed to create encryption key: {e}")
            raise
    
    def _encrypt_data(self, data: Dict[str, Any]) -> bytes:
        """
        Encrypt session data.
        
        Args:
            data: Dictionary of session data
            
        Returns:
            Encrypted data as bytes
        """
        if not CRYPTO_AVAILABLE:
            # Store as plain JSON if crypto not available
            return json.dumps(data).encode('utf-8')
        
        key = self._get_or_create_key()
        fernet = Fernet(key)
        
        json_data = json.dumps(data).encode('utf-8')
        encrypted_data = fernet.encrypt(json_data)
        return encrypted_data
    
    def _decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Decrypt session data.
        
        Args:
            encrypted_data: Encrypted data as bytes
            
        Returns:
            Decrypted session data dictionary
        """
        if not CRYPTO_AVAILABLE:
            # Load as plain JSON if crypto not available
            return json.loads(encrypted_data.decode('utf-8'))
        
        key = self._get_or_create_key()
        fernet = Fernet(key)
        
        try:
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to decrypt session data: {e}")
            raise
    
    def save_session(self, cookies: list, local_storage: Optional[Dict] = None) -> bool:
        """
        Save session data securely.
        
        Args:
            cookies: List of cookie dictionaries
            local_storage: Optional local storage data
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            session_data = {
                "cookies": cookies,
                "local_storage": local_storage or {}
            }
            
            # Validate session data
            if not self._validate_session_data(session_data):
                logger.error("Session data validation failed")
                return False
            
            # Encrypt and save data
            encrypted_data = self._encrypt_data(session_data)
            
            with open(self.session_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions on session file
            os.chmod(self.session_file, stat.S_IRUSR | stat.S_IWUSR)  # 600 - owner read/write only
            
            logger.info("Session data saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")
            return False
    
    def load_session(self) -> Optional[Dict[str, Any]]:
        """
        Load session data securely.
        
        Returns:
            Session data dictionary or None if not available/invalid
        """
        if not self.session_file.exists():
            logger.debug("No session file found")
            return None
        
        try:
            with open(self.session_file, 'rb') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                logger.warning("Session file is empty")
                return None
            
            # Decrypt and validate data
            session_data = self._decrypt_data(encrypted_data)
            
            if not self._validate_session_data(session_data):
                logger.warning("Loaded session data is invalid")
                return None
            
            logger.debug("Session data loaded successfully")
            return session_data
            
        except Exception as e:
            logger.warning(f"Failed to load session data: {e}")
            return None
    
    def _validate_session_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate session data structure.
        
        Args:
            data: Session data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        if not isinstance(data, dict):
            return False
        
        if "cookies" not in data:
            return False
        
        cookies = data["cookies"]
        if not isinstance(cookies, list):
            return False
        
        # Validate each cookie has required fields
        required_cookie_fields = {"name", "value", "domain"}
        for cookie in cookies:
            if not isinstance(cookie, dict):
                return False
            if not required_cookie_fields.issubset(cookie.keys()):
                return False
        
        return True
    
    def clear_session(self) -> bool:
        """
        Clear stored session data.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("Session data cleared")
            
            if self.key_file.exists():
                self.key_file.unlink()
                logger.info("Encryption key cleared")
            
            return True
        except Exception as e:
            logger.error(f"Failed to clear session data: {e}")
            return False
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.
        
        Returns:
            Dictionary with session metadata
        """
        info = {
            "session_exists": self.session_file.exists(),
            "encrypted": CRYPTO_AVAILABLE,
            "session_file": str(self.session_file),
        }
        
        if info["session_exists"]:
            try:
                stat_info = self.session_file.stat()
                info["created"] = stat_info.st_ctime
                info["modified"] = stat_info.st_mtime
                info["size"] = stat_info.st_size
            except Exception as e:
                logger.warning(f"Could not get session file info: {e}")
        
        return info

# Global session manager instance
_session_manager = None

def get_session_manager(session_path: str = None) -> SecureSessionManager:
    """
    Get the global session manager instance.
    
    Args:
        session_path: Optional custom session path
        
    Returns:
        SecureSessionManager instance
    """
    global _session_manager
    
    if _session_manager is None or session_path:
        if session_path:
            _session_manager = SecureSessionManager(session_path)
        else:
            # Use SESSION_PATH environment variable or default
            default_path = os.path.join(os.getenv("SESSION_PATH", "checkin"))
            _session_manager = SecureSessionManager(default_path)
    
    return _session_manager

# Backward compatibility functions
def load_session() -> Optional[Dict[str, Any]]:
    """Load session data (backward compatibility function)."""
    return get_session_manager().load_session()

def save_session(cookies: list, local_storage: Optional[Dict] = None) -> bool:
    """Save session data (backward compatibility function)."""
    return get_session_manager().save_session(cookies, local_storage)