from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx
from urllib.parse import urlencode
from typing import Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"

# Google OAuth URLs
GOOGLE_OAUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL = "https://www.googleapis.com/oauth2/v1/userinfo"


app = FastAPI()

# CORS middleware to allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GoogleUser(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "FastAPI OAuth Backend"}


@app.get("/auth/google/login")
def google_login():
    """Generate Google OAuth login URL"""
    params = {
        "response_type": "code",
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "scope": "openid profile email",
        "access_type": "offline",
    }

    auth_url = f"{GOOGLE_OAUTH_URL}?{urlencode(params)}"
    return {"auth_url": auth_url}


@app.get("/auth/google/callback")
async def google_callback(code: str):
    """Handle Google OAuth callback and exchange code for tokens"""

    # Exchange authorization code for access token
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        # Get access token
        token_response = await client.post(GOOGLE_TOKEN_URL, data=token_data)

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code for token: {token_response.text}",
            )

        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from Google",
            )

        # Get user information
        user_response = await client.get(
            GOOGLE_USER_URL, headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user info from Google: {user_response.text}",
            )

        user_info = user_response.json()

        # Validate Google user data
        try:
            google_user = GoogleUser.model_validate(user_info)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user data from Google: {str(e)}",
            )

        # Return HTML response that sends user data to parent window
        return HTMLResponse(
            content=f"""
        <html>
            <body>
                <script>
                    const userData = {{
                        id: '{google_user.id}',
                        email: '{google_user.email}',
                        name: '{google_user.name}',
                        picture: '{google_user.picture or ""}'
                    }};
                    
                    window.opener.postMessage({{
                        type: 'OAUTH_SUCCESS',
                        user: userData
                    }}, 'http://localhost:3000');
                    
                    window.close();
                </script>
                <p>Login successful! This window should close automatically.</p>
            </body>
        </html>
        """
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
