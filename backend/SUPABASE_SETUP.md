# Supabase Setup Guide

## Getting Your JWT Secret

Your backend needs the Supabase JWT secret to verify authentication tokens from the frontend.

### Step 1: Access Supabase Dashboard

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Select your project: `loxhjltxydpwqnfpwdaa`

### Step 2: Find JWT Secret

1. Click on the **Settings** icon (gear icon) in the left sidebar
2. Click on **API** in the settings menu
3. Scroll down to the **JWT Settings** section
4. Copy the **JWT Secret** value

### Step 3: Update Your .env File

Open `/backend/.env` and replace the placeholder:

```env
SUPABASE_JWT_SECRET=your-actual-jwt-secret-here
```

**IMPORTANT:** Never commit this secret to git! The `.env` file is already in `.gitignore`.

---

## How Authentication Works

### Flow Overview

```
Frontend (React)          Backend (Flask)         MongoDB
    |                          |                     |
    |--1. Login via Supabase-->|                     |
    |<--2. JWT Token-----------|                     |
    |                          |                     |
    |--3. API Request--------->|                     |
    |   (with JWT in header)   |                     |
    |                          |--4. Verify JWT----->|
    |                          |<--5. User Data------|
    |<--6. Response------------|                     |
```

### Step-by-Step

1. **User logs in** via Supabase Auth on the frontend
2. **Supabase returns** a JWT token to the frontend
3. **Frontend sends** the JWT token with every API request to your backend
4. **Backend verifies** the JWT token using the secret
5. **Backend extracts** the user ID from the token
6. **Backend queries** MongoDB using the user ID
7. **Backend returns** the requested data

---

## Testing Authentication

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
python main.py
```

You should see:
```
✓ Successfully connected to MongoDB database: nodelink
✓ MongoDB connection established
 * Running on http://0.0.0.0:5001
```

### 3. Test from Frontend

From your Next.js frontend:

```javascript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'test@example.com',
  password: 'password'
});

if (data.session) {
  const token = data.session.access_token;

  // Initialize user in MongoDB
  const response = await fetch('http://localhost:5001/api/v2/user/init', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const result = await response.json();
  console.log(result); // Should show user initialized
}
```

### 4. Test with cURL (Advanced)

First, get a JWT token by logging in via your frontend, then:

```bash
# Replace YOUR_JWT_TOKEN with the actual token
curl -X POST http://localhost:5001/api/v2/user/init \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Expected response:
```json
{
  "status": "success",
  "message": "User initialized",
  "user": {
    "supabase_user_id": "uuid",
    "email": "user@example.com"
  }
}
```

---

## Common Issues

### "Invalid token" Error

**Problem:** Backend returns 401 with "Invalid token"

**Solutions:**
1. Make sure you copied the correct JWT Secret from Supabase
2. Verify the secret is in the `.env` file without quotes or extra spaces
3. Restart the Flask server after updating `.env`

### "No authorization header" Error

**Problem:** Backend returns 401 with "No authorization header"

**Solutions:**
1. Make sure you're sending the `Authorization` header
2. Format must be: `Authorization: Bearer <token>`
3. Check that the token isn't expired (Supabase tokens expire after 1 hour by default)

### "User not found in database" Error

**Problem:** Backend returns 404 when accessing `/api/v2/user/me`

**Solutions:**
1. Call `/api/v2/user/init` first to create the user in MongoDB
2. This should be called automatically when a user signs up

---

## Security Best Practices

### Production Checklist

- [ ] Never commit `.env` file to git
- [ ] Use environment variables in production (not `.env` files)
- [ ] Enable row-level security (RLS) in Supabase
- [ ] Use HTTPS in production
- [ ] Implement rate limiting on your API
- [ ] Validate all user input
- [ ] Use proper CORS settings (not `CORS(app)` wildcard)

### Recommended CORS Configuration for Production

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/v2/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

## Next Steps

1. ✅ Get JWT Secret from Supabase
2. ✅ Update `.env` file
3. ✅ Install dependencies
4. ✅ Start the backend
5. 🔲 Test user initialization
6. 🔲 Integrate frontend with new API endpoints
7. 🔲 Build your workflow UI

For detailed API documentation, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
