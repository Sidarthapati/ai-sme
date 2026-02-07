"""
Google OAuth authentication helpers.
"""

from google.auth.transport import requests
from google.oauth2 import id_token
from ..config import settings
from ..utils import log
from typing import Dict, Optional

# Google OAuth Client ID from environment
GOOGLE_CLIENT_ID = settings.google_client_id


def verify_google_token(token: str) -> Dict:
    """
    Verify Google ID token and return user info.
    
    Args:
        token: Google ID token from frontend
        
    Returns:
        Dictionary with user info (email, name, picture, etc.)
        
    Raises:
        ValueError: If token is invalid
    """
    try:
        if not GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID not configured")
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Verify issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return {
            'email': idinfo.get('email'),
            'name': idinfo.get('name'),
            'picture': idinfo.get('picture'),
            'google_id': idinfo.get('sub'),
            'email_verified': idinfo.get('email_verified', False),
        }
        
    except ValueError as e:
        log.error(f"Google token verification failed: {e}")
        raise
    except Exception as e:
        log.error(f"Unexpected error verifying Google token: {e}")
        raise ValueError(f"Token verification failed: {str(e)}")


def get_user_info(token: str) -> Optional[Dict]:
    """
    Get user info from Google token.
    Returns None if token is invalid.
    """
    try:
        return verify_google_token(token)
    except Exception:
        return None
