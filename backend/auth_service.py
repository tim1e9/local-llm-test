import requests
import os
from dotenv import load_dotenv
from token_verifier import TokenVerifier
from db_service import DatabaseService

load_dotenv()


class AuthService:
    def __init__(self):
        self.token_verifier = TokenVerifier()
        self.db = DatabaseService()
        self.oidc_provider_url = os.getenv('OIDC_PROVIDER_URL', '')
        self.client_id = os.getenv('OIDC_CLIENT_ID', '')
        self.client_secret = os.getenv('OIDC_CLIENT_SECRET', '')

    def get_authorization_url(self):
        """Get the OIDC authorization URL."""
        redirect_uri = os.getenv('OIDC_REDIRECT_URI', 'http://localhost:5000/callback')
        state = "random-state-string"  # In production, use a secure random state
        return (
            f"{self.oidc_provider_url}/authorize"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&scope=openid profile email roles"
        )

    def exchange_code_for_token(self, code):
        """Exchange authorization code for OIDC token."""
        redirect_uri = os.getenv('OIDC_REDIRECT_URI', 'http://localhost:5000/callback')
        try:
            response = requests.post(
                f"{self.oidc_provider_url}/token",
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                }
            )
            return response.json() if response.status_code == 200 else None
        except requests.RequestException:
            return None

    def handle_callback(self, code):
        """Handle the OAuth callback and create session token."""
        oidc_token = self.exchange_code_for_token(code)
        if not oidc_token:
            return None

        # Extract user info from OIDC token
        user_info = oidc_token.get('userinfo', {})
        username = user_info.get('username', user_info.get('preferred_username', ''))

        if not username:
            return None

        # Get or create user in local database
        user = self.db.get_user_by_username(username)
        if not user:
            user_id = self.db.create_user(
                username=username,
                email=user_info.get('email', ''),
                full_name=user_info.get('name', username),
                manager_id=None  # Will be set by admin or synced later
            )
            if user_id:
                self.db.assign_role_to_user(user_id, 'EMPLOYEE')
                user = self.db.get_user_by_username(username)

        if not user:
            return None

        # Get user roles from OIDC provider
        roles = user_info.get('roles', [])
        if roles:
            for role in roles:
                self.db.assign_role_to_user(user['id'], role)
        else:
            roles = [r['name'] for r in self.db.get_user_roles(user['id'])]

        # Create local JWT token
        jwt_token = self.token_verifier.create_token(user['id'], user['username'], self.db.get_user_roles(user['id']))
        return jwt_token

    def verify_request_token(self, token):
        """Verify a JWT token from a request."""
        return self.token_verifier.verify_token(token)
