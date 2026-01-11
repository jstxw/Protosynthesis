# Authentication Setup Guide

This document explains the authentication system that has been integrated into your Next.js project.

## What Was Copied

### 1. Auth System
- **`contexts/AuthContext.tsx`** - Manages authentication state using Supabase
- **`lib/supabase.ts`** - Supabase client configuration
- **`services/api.ts`** - API client with automatic auth token injection

### 2. Pages (Next.js App Router)
- **`app/login/page.tsx`** - Login page with email/password and social auth
- **`app/signup/page.tsx`** - Sign up page with password strength indicator
- **`app/dashboard/page.tsx`** - Protected dashboard with project management

### 3. Supporting Files
- **`components/Providers.tsx`** - Client-side auth provider wrapper
- **`types/api.ts`** - TypeScript types for API responses
- **`.env.example`** - Environment variable template
- **`tailwind.config.js`** - Complete design system configuration
- **`app/globals.css`** - All component styles (buttons, forms, etc.)

### 4. Dependencies Added
- `@supabase/supabase-js` - Supabase authentication
- `lucide-react` - Icon library

## Setup Instructions

### Step 1: Environment Variables

1. Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```

2. Get your Supabase credentials from [supabase.com](https://supabase.com):
   - Create a new project (or use existing)
   - Go to Project Settings → API
   - Copy the Project URL and anon/public key

3. Update `.env.local`:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
   NEXT_PUBLIC_API_BASE_URL=http://localhost:5001/api
   ```

### Step 2: Supabase Setup

1. In your Supabase project, go to **Authentication → Providers**
2. Enable Email provider
3. (Optional) Enable Google and/or GitHub providers for social login

### Step 3: Backend MongoDB Integration

The auth system expects these backend endpoints (you'll need to create them):

- `POST /auth/create-profile` - Creates user profile in MongoDB after Supabase signup
  ```json
  {
    "supabase_user_id": "uuid",
    "email": "user@example.com",
    "full_name": "User Name"
  }
  ```

- `POST /auth/update-last-login` - Updates last login timestamp
  ```json
  {
    "supabase_user_id": "uuid"
  }
  ```

### Step 4: Test the Flow

1. Start your backend server (should be running on port 5001)
2. Start Next.js: `npm run dev`
3. Navigate to `http://localhost:3000`
4. You should be redirected to `/login`
5. Create an account at `/signup`
6. After signup, you'll be redirected to `/dashboard`

## File Structure

```
frontend/
├── app/
│   ├── login/
│   │   └── page.tsx          # Login page
│   ├── signup/
│   │   └── page.tsx          # Sign up page
│   ├── dashboard/
│   │   └── page.tsx          # Dashboard (protected)
│   ├── layout.js             # Root layout with AuthProvider
│   ├── page.js               # Home page (redirects to /login)
│   └── globals.css           # All styles
├── components/
│   └── Providers.tsx         # Auth provider wrapper
├── contexts/
│   └── AuthContext.tsx       # Auth state management
├── lib/
│   └── supabase.ts          # Supabase client
├── services/
│   └── api.ts               # API client with auth
├── types/
│   ├── api.ts               # API type definitions
│   └── index.ts
└── .env.example             # Environment template
```

## Key Features

### Authentication
- ✅ Email/password authentication via Supabase
- ✅ Social login placeholders (Google, GitHub)
- ✅ Protected routes
- ✅ Automatic token management
- ✅ Session persistence

### Login Page (`/login`)
- Email and password inputs
- Password visibility toggle
- Social login buttons
- Error handling
- Link to signup page

### Sign Up Page (`/signup`)
- Full name, email, password inputs
- Password confirmation
- Password strength indicator
- Terms & conditions checkbox
- Link to login page

### Dashboard Page (`/dashboard`)
- Protected route (redirects to login if not authenticated)
- User welcome message
- Project management interface
- New project modal with templates
- Search and sort functionality
- Logout button

## Next Steps

### 1. Backend Integration
Create the MongoDB endpoints mentioned in Step 3 above.

### 2. Copy Public Assets
If you want the icons/images from the old project:
```bash
cp -r /Users/jstwx07/Desktop/projects/NodeLink_DH/frontend/public/icons ./public/
```

### 3. Protect More Routes
To protect additional routes, wrap them with auth checks in their page files:
```tsx
'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function ProtectedPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) return <div>Loading...</div>;
  if (!user) return null;

  return <div>Your protected content</div>;
}
```

### 4. Customize
- Update colors in `tailwind.config.js`
- Modify branding in login/signup pages
- Add your logo to `/public/icons/logo.svg`
- Customize dashboard templates

## Troubleshooting

### "Module not found" errors
Make sure you're in the frontend directory and run:
```bash
npm install
```

### Supabase connection errors
- Check that environment variables are set correctly
- Verify Supabase project is active
- Check browser console for detailed error messages

### Redirecting issues
- Clear browser localStorage
- Check that AuthProvider is wrapping your app in layout.js

## Technologies Used

- **Next.js 16** - App Router
- **Supabase** - Authentication
- **Tailwind CSS 4** - Styling
- **Lucide React** - Icons
- **TypeScript** - Type safety

---

Need help? Check the console logs - the auth system includes detailed logging for debugging!
