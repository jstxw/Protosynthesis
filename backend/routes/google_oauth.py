"""
Google OAuth 2.0 routes for Google Calendar integration.

Provides endpoints to:
1. Initiate Google OAuth consent flow
2. Handle the callback and store tokens
3. Check authentication status
"""

import os
import json
from flask import Blueprint, redirect, request, jsonify
from dotenv import load_dotenv, set_key, find_dotenv

# Allow HTTP for local development (OAuth normally requires HTTPS)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

google_oauth_bp = Blueprint('google_oauth', __name__, url_prefix='/api/v2/google')

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
REDIRECT_URI = 'http://localhost:5001/api/v2/google/callback'
TOKEN_ENV_KEY = 'READ_GOOGLE_CALENDAR_TOKEN'
REFRESH_TOKEN_ENV_KEY = 'GOOGLE_REFRESH_TOKEN'


def _get_client_config():
    """Get OAuth client configuration from environment variables."""
    client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
    if not client_id or not client_secret:
        return None
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }
    }


@google_oauth_bp.route('/auth', methods=['GET'])
def google_auth():
    """
    Redirects the user to Google's OAuth 2.0 consent screen.
    Visit this URL in a browser to begin authorization.
    """
    from google_auth_oauthlib.flow import Flow

    client_config = _get_client_config()
    if not client_config:
        return jsonify({
            "error": "Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
        }), 500

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',      # Get a refresh token
        include_granted_scopes='true',
        prompt='consent'            # Force consent to ensure refresh token
    )

    # Store state in environment temporarily for CSRF validation
    os.environ['GOOGLE_OAUTH_STATE'] = state

    return redirect(authorization_url)


@google_oauth_bp.route('/callback', methods=['GET'])
def google_callback():
    """
    Handles the OAuth 2.0 callback from Google.
    Exchanges the authorization code for access and refresh tokens,
    then saves them to .env for use by the ApiKeyBlock.
    """
    from google_auth_oauthlib.flow import Flow

    client_config = _get_client_config()
    if not client_config:
        return jsonify({"error": "Google OAuth not configured"}), 500

    # Check for error from Google
    error = request.args.get('error')
    if error:
        return jsonify({"error": f"Google authorization failed: {error}"}), 400

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    # Exchange authorization code for tokens
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    access_token = credentials.token
    refresh_token = credentials.refresh_token

    # Save tokens to .env file so they persist across restarts
    dotenv_path = find_dotenv()
    if not dotenv_path:
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

    # Store access token with READ_ prefix so ApiKeyBlock can find it
    token_value = f"Bearer {access_token}"
    set_key(dotenv_path, TOKEN_ENV_KEY, token_value)
    os.environ[TOKEN_ENV_KEY] = token_value

    # Store refresh token (without READ_ prefix — internal use only)
    if refresh_token:
        set_key(dotenv_path, REFRESH_TOKEN_ENV_KEY, refresh_token)
        os.environ[REFRESH_TOKEN_ENV_KEY] = refresh_token

    # Store token expiry for reference
    if credentials.expiry:
        expiry_str = credentials.expiry.isoformat()
        set_key(dotenv_path, 'GOOGLE_TOKEN_EXPIRY', expiry_str)
        os.environ['GOOGLE_TOKEN_EXPIRY'] = expiry_str

    print(f"✅ Google Calendar OAuth complete! Token saved to {TOKEN_ENV_KEY}")

    return """
    <html>
    <head><title>Google Calendar Connected</title></head>
    <body style="font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #0a0a0a; color: #fff;">
        <div style="text-align: center; padding: 2rem;">
            <h1 style="color: #4ade80;">✅ Google Calendar Connected!</h1>
            <p style="color: #a1a1aa;">Your access token has been saved. You can now use the Google Calendar API block in your workflows.</p>
            <p style="color: #a1a1aa; font-size: 0.875rem;">Use an <strong>API Key block</strong> and select <code>GOOGLE_CALENDAR_TOKEN</code> to inject the token.</p>
            <p style="margin-top: 2rem;"><a href="javascript:window.close()" style="color: #60a5fa;">Close this tab</a></p>
        </div>
    </body>
    </html>
    """


@google_oauth_bp.route('/status', methods=['GET'])
def google_status():
    """
    Returns whether a Google Calendar OAuth token is currently available.
    """
    token = os.getenv(TOKEN_ENV_KEY)
    has_refresh = bool(os.getenv(REFRESH_TOKEN_ENV_KEY))
    expiry = os.getenv('GOOGLE_TOKEN_EXPIRY', '')

    return jsonify({
        "authenticated": bool(token and token.strip()),
        "has_refresh_token": has_refresh,
        "token_expiry": expiry,
        "env_key": "GOOGLE_CALENDAR_TOKEN",
        "message": "Use an API Key block with 'GOOGLE_CALENDAR_TOKEN' to inject the token into your Calendar API block."
    })


@google_oauth_bp.route('/refresh', methods=['POST'])
def google_refresh():
    """
    Refreshes the Google OAuth access token using the stored refresh token.
    Call this if the access token has expired.
    """
    import google.auth.transport.requests
    from google.oauth2.credentials import Credentials

    refresh_token = os.getenv(REFRESH_TOKEN_ENV_KEY)
    if not refresh_token:
        return jsonify({"error": "No refresh token stored. Re-authorize at /api/v2/google/auth"}), 400

    client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')

    if not client_id or not client_secret:
        return jsonify({"error": "Google OAuth not configured"}), 500

    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri='https://oauth2.googleapis.com/token'
        )

        creds.refresh(google.auth.transport.requests.Request())

        # Update stored token
        dotenv_path = find_dotenv()
        token_value = f"Bearer {creds.token}"
        set_key(dotenv_path, TOKEN_ENV_KEY, token_value)
        os.environ[TOKEN_ENV_KEY] = token_value

        if creds.expiry:
            expiry_str = creds.expiry.isoformat()
            set_key(dotenv_path, 'GOOGLE_TOKEN_EXPIRY', expiry_str)
            os.environ['GOOGLE_TOKEN_EXPIRY'] = expiry_str

        print(f"🔄 Google Calendar token refreshed successfully")

        return jsonify({
            "status": "refreshed",
            "token_expiry": creds.expiry.isoformat() if creds.expiry else None
        })

    except Exception as e:
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500
