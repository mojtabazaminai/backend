
import httpx

from ...core.config import settings
from ...schemas.auth import GoogleUserInfo


class GoogleProvider:
    def __init__(self) -> None:
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_url = settings.GOOGLE_REDIRECT_URL
        self.token_endpoint = "https://oauth2.googleapis.com/token"
        self.userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"

    async def get_user_data(self, code: str) -> GoogleUserInfo:
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_data = {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_url,
                "grant_type": "authorization_code",
            }
            token_response = await client.post(self.token_endpoint, data=token_data)
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]

            # Get user info
            user_response = await client.get(
                self.userinfo_endpoint, headers={"Authorization": f"Bearer {access_token}"}
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            return GoogleUserInfo(**user_data)
