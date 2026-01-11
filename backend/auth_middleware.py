from functools import wraps
from flask import request, jsonify
import jwt
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')
SUPABASE_URL = os.getenv('SUPABASE_URL')

# Debug: Print configuration
if SUPABASE_JWT_SECRET:
    secret_preview = SUPABASE_JWT_SECRET[:10] + "..." + SUPABASE_JWT_SECRET[-10:] if len(SUPABASE_JWT_SECRET) > 20 else "***"
    print(f"🔑 JWT Secret loaded: {secret_preview} (length: {len(SUPABASE_JWT_SECRET)})")
else:
    print("❌ JWT Secret NOT loaded!")

if SUPABASE_URL:
    print(f"🔗 Supabase URL: {SUPABASE_URL}")
else:
    print("❌ Supabase URL NOT loaded!")

# Cache for JWKS
_jwks_cache = None

def get_supabase_jwks():
    """Fetch Supabase's public keys from JWKS endpoint"""
    global _jwks_cache

    if _jwks_cache:
        return _jwks_cache

    try:
        jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        print(f"🔍 Fetching JWKS from: {jwks_url}")

        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        jwks = response.json()

        print(f"✅ JWKS fetched: {len(jwks.get('keys', []))} keys found")
        _jwks_cache = jwks
        return jwks
    except Exception as e:
        print(f"❌ Failed to fetch JWKS: {e}")
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
        print(f"🔍 Attempting to verify token...")
        print(f"🔍 Token preview: {token[:20]}...{token[-20:]}")
        print(f"🔍 Token length: {len(token)}")

        # Decode header to check algorithm
        header = jwt.get_unverified_header(token)
        algorithm = header.get('alg')
        kid = header.get('kid')

        print(f"🔍 Token algorithm: {algorithm}")
        print(f"🔍 Token kid (key ID): {kid}")

        # Decode without verification to see payload
        unverified = jwt.decode(token, options={"verify_signature": False})
        print(f"🔍 Token issuer: {unverified.get('iss')}")
        print(f"🔍 Token audience: {unverified.get('aud')}")

        # For ES256, we need the public key from JWKS
        if algorithm == 'ES256':
            print(f"🔍 ES256 detected - fetching public key from JWKS...")
            jwks = get_supabase_jwks()

            if not jwks:
                raise ValueError("Could not fetch JWKS from Supabase")

            # Find the matching key
            matching_key = None
            for key in jwks.get('keys', []):
                if kid and key.get('kid') == kid:
                    matching_key = key
                    break
                elif not kid:
                    # Use first key if no kid specified
                    matching_key = key
                    break

            if not matching_key:
                raise ValueError(f"No matching key found for kid: {kid}")

            print(f"✅ Found matching public key")

            # Convert JWK to PEM format for PyJWT
            from jwt import PyJWK
            public_key = PyJWK(matching_key).key

            # Verify with public key
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['ES256'],
                audience='authenticated',
                options={"verify_aud": True}
            )

            print(f"✅ Token verified successfully with ES256!")
            print(f"✅ User ID: {payload.get('sub')}")
            print(f"✅ Email: {payload.get('email')}")
            return payload

        # For HS256, use the JWT secret
        elif algorithm in ['HS256', 'HS384', 'HS512']:
            print(f"🔍 {algorithm} detected - using JWT secret...")

            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=[algorithm],
                audience='authenticated',
                options={"verify_aud": True}
            )

            print(f"✅ Token verified successfully with {algorithm}!")
            print(f"✅ User ID: {payload.get('sub')}")
            print(f"✅ Email: {payload.get('email')}")
            return payload

        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    except jwt.ExpiredSignatureError as e:
        print(f"❌ Token expired: {e}")
        raise ValueError("Token has expired")
    except ValueError:
        raise
    except Exception as e:
        print(f"❌ Token verification error: {type(e).__name__}")
        print(f"❌ Error details: {str(e)}")
        import traceback
        traceback.print_exc()
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
        print(f"\n{'='*60}")
        print(f"🔐 AUTH MIDDLEWARE - Route: {request.path}")
        print(f"{'='*60}")

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            print("❌ No Authorization header found")
            return jsonify({"error": "No authorization header"}), 401

        print(f"✅ Authorization header present")

        try:
            # Extract token (format: "Bearer <token>")
            parts = auth_header.split()

            if len(parts) != 2 or parts[0].lower() != 'bearer':
                print(f"❌ Invalid header format")
                return jsonify({"error": "Invalid authorization header format"}), 401

            token = parts[1]
            print(f"✅ Token extracted from header")

            # Verify the token
            current_user = verify_token(token)

            print(f"✅ Authentication successful for user: {current_user.get('sub')}")
            print(f"{'='*60}\n")

            # Pass the decoded user info to the route handler
            return f(current_user, *args, **kwargs)

        except ValueError as e:
            print(f"❌ ValueError during auth: {e}")
            print(f"{'='*60}\n")
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            print(f"❌ Unexpected error during auth: {type(e).__name__}: {e}")
            print(f"{'='*60}\n")
            return jsonify({"error": "Authentication failed"}), 401

    return decorated_function

def get_user_id_from_token() -> str:
    """
    Extract user ID from the current request's JWT token.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise ValueError("No authorization header")

    token = auth_header.split()[1]
    payload = verify_token(token)
    return payload['sub']
