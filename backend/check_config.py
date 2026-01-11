#!/usr/bin/env python3
"""
Diagnostic script to check Supabase JWT configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("="*60)
print("🔍 CONFIGURATION DIAGNOSTICS")
print("="*60)

# Check JWT Secret
jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
print(f"\n1️⃣  JWT Secret Status:")
if jwt_secret:
    print(f"   ✅ JWT Secret is loaded")
    print(f"   📏 Length: {len(jwt_secret)} characters")

    # Check if it's a token (wrong) or a secret (correct)
    if jwt_secret.startswith('eyJ'):
        print(f"   ❌ ERROR: This looks like a JWT TOKEN, not a secret!")
        print(f"   ❌ It starts with 'eyJ' which indicates a token")
        print(f"   💡 You need the JWT SECRET from Supabase Settings → API → JWT Settings")
    else:
        print(f"   ✅ Looks like a proper JWT secret (doesn't start with 'eyJ')")
        preview = jwt_secret[:10] + "..." + jwt_secret[-10:]
        print(f"   🔑 Preview: {preview}")
else:
    print(f"   ❌ JWT Secret NOT found in .env file!")

# Check other Supabase config
print(f"\n2️⃣  Supabase URL:")
supabase_url = os.getenv('SUPABASE_URL')
if supabase_url:
    print(f"   ✅ {supabase_url}")
else:
    print(f"   ❌ Not set")

print(f"\n3️⃣  Supabase Anon Key:")
supabase_key = os.getenv('SUPABASE_KEY')
if supabase_key:
    print(f"   ✅ Loaded (length: {len(supabase_key)})")
else:
    print(f"   ❌ Not set")

# Check MongoDB
print(f"\n4️⃣  MongoDB URI:")
mongodb_uri = os.getenv('MONGODB_URI')
if mongodb_uri:
    # Mask password
    if '@' in mongodb_uri:
        parts = mongodb_uri.split('@')
        masked = parts[0].split(':')[0] + ':***@' + parts[1]
        print(f"   ✅ {masked}")
    else:
        print(f"   ✅ Set")
else:
    print(f"   ❌ Not set")

print(f"\n5️⃣  MongoDB Database:")
mongodb_db = os.getenv('MONGODB_DB_NAME')
if mongodb_db:
    print(f"   ✅ {mongodb_db}")
else:
    print(f"   ⚠️  Not set (will use default: nodelink)")

print("\n" + "="*60)
print("📋 SUMMARY")
print("="*60)

issues = []

if not jwt_secret:
    issues.append("❌ JWT Secret is missing")
elif jwt_secret.startswith('eyJ'):
    issues.append("❌ JWT Secret is actually a token (wrong value)")

if not supabase_url:
    issues.append("❌ Supabase URL is missing")

if not mongodb_uri:
    issues.append("❌ MongoDB URI is missing")

if issues:
    print("\n🚨 ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
    print("\n💡 Fix these issues before running the backend!")
else:
    print("\n✅ All configuration looks good!")
    print("   You can start the backend server.")

print("="*60)
