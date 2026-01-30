# utils/auth_manager.py
"""
Authentication manager with persistent login
Stores user session securely
"""

import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta


class AuthManager:
    """Manages user authentication and persistent sessions"""
    
    SESSION_FILE = "user_session.json"
    SESSION_DURATION_DAYS = 30  # Auto-logout after 30 days
    
    @staticmethod
    def _encrypt_data(data: str, salt: str = None) -> tuple:
        """Simple encryption for session data"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Create a hash of the data with salt
        combined = f"{data}{salt}".encode('utf-8')
        hashed = hashlib.sha256(combined).hexdigest()
        return hashed, salt
    
    @staticmethod
    def _generate_session_token() -> str:
        """Generate a secure random session token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def save_session(username: str, remember_me: bool = True):
        """
        Save user session to file
        
        Args:
            username: The logged-in username
            remember_me: Whether to persist the session
        """
        if not remember_me:
            AuthManager.clear_session()
            return
        
        session_token = AuthManager._generate_session_token()
        encrypted_username, salt = AuthManager._encrypt_data(username)
        
        session_data = {
            "username": username,  # Store in plain text for convenience
            "encrypted_username": encrypted_username,
            "salt": salt,
            "session_token": session_token,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=AuthManager.SESSION_DURATION_DAYS)).isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        try:
            with open(AuthManager.SESSION_FILE, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Set file permissions to read/write for owner only (Unix-like systems)
            try:
                os.chmod(AuthManager.SESSION_FILE, 0o600)
            except:
                pass  # Windows doesn't support chmod
            
            print(f"✓ Session saved for user: {username}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to save session: {e}")
            return False
    
    @staticmethod
    def load_session() -> dict:
        """
        Load user session from file
        
        Returns:
            dict with session data or None if no valid session
        """
        if not os.path.exists(AuthManager.SESSION_FILE):
            print("No session file found")
            return None
        
        try:
            with open(AuthManager.SESSION_FILE, 'r') as f:
                session_data = json.load(f)
            
            # Check if session has expired
            expires_at = datetime.fromisoformat(session_data.get('expires_at', ''))
            
            if datetime.now() > expires_at:
                print("Session expired")
                AuthManager.clear_session()
                return None
            
            # Update last activity
            session_data['last_activity'] = datetime.now().isoformat()
            with open(AuthManager.SESSION_FILE, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print(f"✓ Session loaded for user: {session_data.get('username')}")
            return session_data
            
        except Exception as e:
            print(f"✗ Failed to load session: {e}")
            AuthManager.clear_session()
            return None
    
    @staticmethod
    def clear_session():
        """Clear the saved session (logout)"""
        try:
            if os.path.exists(AuthManager.SESSION_FILE):
                os.remove(AuthManager.SESSION_FILE)
                print("✓ Session cleared")
            return True
        except Exception as e:
            print(f"✗ Failed to clear session: {e}")
            return False
    
    @staticmethod
    def is_session_valid() -> bool:
        """Check if there's a valid session"""
        session = AuthManager.load_session()
        return session is not None
    
    @staticmethod
    def get_logged_in_user() -> str:
        """Get the currently logged-in username from session"""
        session = AuthManager.load_session()
        if session:
            return session.get('username')
        return None
    
    @staticmethod
    def update_session_activity():
        """Update the last activity timestamp"""
        session = AuthManager.load_session()
        if session:
            session['last_activity'] = datetime.now().isoformat()
            try:
                with open(AuthManager.SESSION_FILE, 'w') as f:
                    json.dump(session, f, indent=2)
            except:
                pass


