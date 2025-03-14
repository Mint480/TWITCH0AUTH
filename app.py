import os
import requests
from flask import Flask, redirect, request, session, url_for
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
# Load environment variables
load_dotenv()

# Twitch OAuth Details
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
AUTH_URL = os.getenv("AUTH_URL")
TOKEN_URL = os.getenv("TOKEN_URL").strip()  # Remove extra spaces

print(f"TOKEN_URL: '{TOKEN_URL}'")  # Debugging

print(f"Client ID: {CLIENT_ID}")  # Do not print secrets in production
# Define OAuth scopes (modify if needed)
SCOPES = "user:read:email"  # Add more scopes if required

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: No code provided", 400

    print(f"Received code: {code}")  # Debugging

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    print("Sending request to:", TOKEN_URL)
    print("With data:", data)

    response = requests.post(TOKEN_URL, data=data, headers=headers)
    token_data = response.json()

    print("Response:", token_data)  # Debugging

    if "access_token" in token_data:
        os.environ["TWITCH_ACCESS_TOKEN"] = token_data["access_token"]
        os.environ["TWITCH_REFRESH_TOKEN"] = token_data["refresh_token"]
        return redirect("https://discord.com/app")
    else:
        return f"Error: {token_data}", 400

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
