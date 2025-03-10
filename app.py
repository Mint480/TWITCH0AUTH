import os
import requests
from flask import Flask, redirect, request, session, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Twitch OAuth Details
CLIENT_ID = "r0sd7izv5d9wcncznweyms52wq0z6k"
CLIENT_SECRET = "y36nl69gyype6ac433ja02zpqm6mv7"
REDIRECT_URI = "https://twitch0auth-production.up.railway.app/callback"  # Change this after deployment
AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

# Define OAuth scopes (modify if needed)
SCOPES = "user:read:email"  # Add more scopes if required


@app.route("/")
def home():
    """Redirects to Twitch for OAuth authentication."""
    auth_url = (
        f"{AUTH_URL}?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code&scope={SCOPES}"
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """Handles the Twitch OAuth callback and saves refresh token."""
    code = request.args.get("code")
    if not code:
        return "Error: No code provided", 400  # ❌ No code returned

    # Exchange code for access + refresh tokens
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post(TOKEN_URL, data=data)
    token_data = response.json()

    if "access_token" in token_data:
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]  # ✅ Store this!

        # Save tokens securely (e.g., database or environment variables)
        os.environ["TWITCH_ACCESS_TOKEN"] = access_token
        os.environ["TWITCH_REFRESH_TOKEN"] = refresh_token

        return f"Success! Access Token: {access_token}<br>Refresh Token: {refresh_token}"
    else:
        return f"Error: {token_data}", 400  # ❌ Something went wrong

def refresh_access_token():
    """Refreshes the Twitch access token when it expires."""
    refresh_token = os.getenv("TWITCH_REFRESH_TOKEN")
    if not refresh_token:
        return "Error: No refresh token available"

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    response = requests.post(TOKEN_URL, data=data)
    new_token_data = response.json()

    if "access_token" in new_token_data:
        new_access_token = new_token_data["access_token"]
        new_refresh_token = new_token_data["refresh_token"]

        # Update stored tokens
        os.environ["TWITCH_ACCESS_TOKEN"] = new_access_token
        os.environ["TWITCH_REFRESH_TOKEN"] = new_refresh_token

        print("✅ Access token refreshed successfully!")
        return new_access_token
    else:
        print("❌ Failed to refresh token:", new_token_data)
        return None

def make_twitch_request(url):
    """Makes a Twitch API request and refreshes token if expired."""
    headers = {
        "Authorization": f"Bearer {os.getenv('TWITCH_ACCESS_TOKEN')}",
        "Client-Id": CLIENT_ID
    }
    
    response = requests.get(url, headers=headers)
    
    # If token expired, refresh and retry
    if response.status_code == 401:  # Unauthorized = Token expired
        print("🔄 Token expired, refreshing...")
        new_token = refresh_access_token()
        if new_token:
            headers["Authorization"] = f"Bearer {new_token}"
            response = requests.get(url, headers=headers)

    return response.json()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
