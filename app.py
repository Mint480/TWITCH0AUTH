import os
import requests
from flask import Flask, redirect, request, session, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Twitch OAuth Details
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"
REDIRECT_URI = "https://yourapp.up.railway.app/callback"  # Change this after deployment
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
    """Handles Twitch OAuth callback and retrieves the access token."""
    code = request.args.get("code")
    
    if not code:
        return "Error: No authorization code provided!", 400

    # Exchange code for an access token
    token_response = requests.post(TOKEN_URL, data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    })

    token_data = token_response.json()
    
    if "access_token" not in token_data:
        return f"Error retrieving token: {token_data}", 400

    session["access_token"] = token_data["access_token"]

    return f"Authentication successful! Access Token: {token_data['access_token']}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
