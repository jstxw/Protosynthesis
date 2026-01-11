from functools import wraps
from flask import request, jsonify, g
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from jwt import PyJWK
import os
import requests
from dotenv import load_dotenv
import logging

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')
SUPABASE_URL = os.getenv('SUPABASE_URL')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Print configuration
if SUPABASE_JWT_SECRET:
    secret_preview = SUPABASE_JWT_SECRET[:10] + "..." + SUPABASE_JWT_SECRET[-10:] if len(SUPABASE_JWT_SECRET) > 20 else "***"
    logger.info(f"🔑 JWT Secret loaded: {secret_preview} (length: {len(SUPABASE_JWT_SECRET)})")
else:
    logger.warning("❌ Supabase JWT Secret (HS256) is NOT configured!")

if SUPABASE_URL:
    logger.info(f"🔗 Supabase URL: {SUPABASE_URL}")
else:
    logger.warning("❌ Supabase URL is NOT configured!")

# Cache for JWKS
_jwks_cache = None

def get_supabase_jwks():
    """Fetch Supabase's public keys from JWKS endpoint"""
    global _jwks_cache

    if _jwks_cache:
        return _jwks_cache

    try:
        jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        logger.info(f"🔍 Fetching JWKS from: {jwks_url}")

        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        jwks = response.json()

        logger.info(f"✅ JWKS fetched: {len(jwks.get('keys', []))} keys found")
        _jwks_cache = jwks
        return jwks
    except Exception as e:
        logger.error(f"❌ Failed to fetch JWKS: {e}")
        return None

def _find_matching_key_in_jwks(kid: str, jwks: dict):
    """Finds a matching key in the JWKS based on the key ID (kid)."""
    if not jwks or 'keys' not in jwks:
        return None

    for key in jwks['keys']:
        if kid and key.get('kid') == kid:
            return key

    # Fallback for tokens that might not have a 'kid' in the header
    if not kid and jwks['keys']:
        logger.warning("⚠️ Token header has no 'kid', using the first available key from JWKS.")
        return jwks['keys'][0]

    return None

def verify_token(token: str) -> dict:
    """
    Verify Supabase JWT token using ES256 algorithm and public key from JWKS.

    Args:
        token: JWT token from Authorization header

    Returns:
        dict: Decoded token payload containing user info

    Raises:
        ValueError: If token is invalid or expired
    """
    try:
        logger.info("🔍 Attempting to verify token...")

        # Decode header to check algorithm
        header = jwt.get_unverified_header(token)
        algorithm = header.get('alg')
        kid = header.get('kid')

        logger.info(f"🔍 Token algorithm: {algorithm}, Key ID: {kid}")

        # For ES256, we need the public key from JWKS
        if algorithm == 'ES256':
            logger.info("🔍 ES256 detected - fetching public key from JWKS...")
            jwks = get_supabase_jwks()
            if not jwks:
                raise ValueError("Could not fetch JWKS from Supabase")

            matching_key = _find_matching_key_in_jwks(kid, jwks)
            if not matching_key:
                raise ValueError(f"No matching key found for kid: {kid}")

            logger.info("✅ Found matching public key in JWKS")

            # Convert JWK to PEM format for PyJWT
            public_key = PyJWK(matching_key).key

            # Verify with public key
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['ES256'],
                audience='authenticated',
                options={"verify_aud": True}
            )

            logger.info(f"✅ Token verified successfully with ES256 for user: {payload.get('sub')}")
            return payload

        # For HS256, use the JWT secret
        elif algorithm in ['HS256', 'HS384', 'HS512']:
            logger.info(f"🔍 {algorithm} detected - using JWT secret...")
            if not SUPABASE_JWT_SECRET:
                raise ValueError("HS256 signing secret is not configured on the server.")

            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=[algorithm],
                audience='authenticated',
                options={"verify_aud": True}
            )

            logger.info(f"✅ Token verified successfully with {algorithm} for user: {payload.get('sub')}")
            return payload

        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    except ExpiredSignatureError as e:
        logger.warning(f"❌ Token expired: {e}")
        raise ValueError("Token has expired")
    except InvalidTokenError as e:
        logger.error(f"❌ Invalid token error: {e}")
        raise ValueError(f"Invalid token: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected token verification error: {type(e).__name__}: {e}", exc_info=True)
        raise ValueError(f"Invalid token: {str(e)}")

def require_auth(f):
    """
    Decorator to protect routes with JWT authentication.

    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_route(current_user):
            user_id = current_user['sub']
            email = current_user['email']
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"{'='*60}")
        logger.info(f"🔐 AUTH MIDDLEWARE - Route: {request.path}")
        logger.info(f"{'='*60}")

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            logger.warning("❌ No Authorization header found")
            return jsonify({"error": "No authorization header"}), 401

        logger.info("✅ Authorization header present")

        try:
            # Extract token (format: "Bearer <token>")
            parts = auth_header.split()

            if len(parts) != 2 or parts[0].lower() != 'bearer':
                logger.warning("❌ Invalid header format")
                return jsonify({"error": "Invalid authorization header format"}), 401

            token = parts[1]
            logger.info("✅ Token extracted from header")

            # Verify the token
            current_user = verify_token(token)

            # Store user in Flask's application context for this request
            g.user = current_user

            logger.info(f"✅ Authentication successful for user: {current_user.get('sub')}")
            logger.info(f"{'='*60}\n")

            # Pass the decoded user info to the route handler
            return f(current_user, *args, **kwargs)

        except ValueError as e:
            logger.error(f"❌ Authentication failed (ValueError): {e}")
            logger.info(f"{'='*60}\n")
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            logger.error(f"❌ Unexpected error during auth: {type(e).__name__}: {e}", exc_info=True)
            logger.info(f"{'='*60}\n")
            return jsonify({"error": "Authentication failed"}), 401

    return decorated_function

def get_user_id_from_token() -> str:
    """
    Extract user ID from the current request's context.
    This should be used in a route protected by @require_auth.
    """
    if 'user' in g:
        return g.user.get('sub')
    # This fallback is expensive and should ideally not be hit.
    # It's here for cases where the function might be called outside the decorator's direct flow.
    logger.warning("⚠️ get_user_id_from_token() called without 'g.user', re-verifying token.")
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise ValueError("No authorization header")

        token = auth_header.split()[1]
        payload = verify_token(token)
        return payload['sub']
    except (ValueError, IndexError) as e:
        logger.error(f"Could not get user ID from token: {e}")
        return None
