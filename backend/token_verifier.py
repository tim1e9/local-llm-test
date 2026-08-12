import jwt
import os
import time
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class TokenVerifier:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
        self.algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        self.token_expiry_hours = 8

    def create_token(self, user_id, username, roles):
        """Create a JWT token for an authenticated user."""
        payload = {
            'user_id': user_id,
            'username': username,
            'roles': [r['name'] for r in roles],
            'iat': time.time(),
            'exp': time.time() + (self.token_expiry_hours * 3600)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token):
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def has_role(self, token_payload, required_role):
        """Check if the user has a specific role."""
        if not token_payload:
            return False
        return required_role in token_payload.get('roles', [])
