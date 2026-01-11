'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import type { User, Session } from '@supabase/supabase-js';
import { authHelpers } from '@/lib/supabase';
import { post } from '@/services/api';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signUp: (email: string, password: string, fullName?: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Initialize auth state and listen for changes
  useEffect(() => {
    // Check for existing session
    authHelpers.getSession().then(({ session, error }) => {
      if (!error && session) {
        setSession(session);
        setUser(session.user);
      }
      setLoading(false);
    });

    // Subscribe to auth state changes
    const subscription = authHelpers.onAuthStateChange((session) => {
      setSession(session);
      setUser(session?.user ?? null);
    });

    // Cleanup subscription on unmount
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const signUp = async (email: string, password: string, fullName?: string) => {
    setLoading(true);
    try {
      console.log('🔵 Attempting signup with:', { email, fullName });
      const { data, error } = await authHelpers.signUp(email, password, fullName);

      console.log('🔵 Supabase signup response:', {
        hasUser: !!data.user,
        hasSession: !!data.session,
        error: error?.message
      });

      if (error) {
        console.error('❌ Supabase signup error:', error);
        throw new Error(error.message);
      }

      if (!data.user) {
        console.error('❌ No user returned from Supabase');
        throw new Error('Failed to create user account');
      }

      // Create user profile in backend MongoDB
      try {
        console.log('🟢 Creating backend profile for:', data.user.id);

        // Get the JWT token from the session
        const token = data.session?.access_token;

        if (token) {
          const response = await fetch('http://localhost:5001/api/v2/user/init', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          const result = await response.json();
          console.log('🟢 Backend profile created:', result);
        } else {
          console.warn('⚠️ No token available for backend profile creation');
        }
      } catch (backendError: any) {
        console.error('❌ Failed to create backend profile:', backendError);
        // Don't throw - user is created in Supabase, profile creation can be retried
      }

      setSession(data.session);
      setUser(data.user);

      // Navigate to dashboard
      router.push('/dashboard');
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signIn = async (email: string, password: string) => {
    setLoading(true);
    try {
      const { data, error } = await authHelpers.signIn(email, password);

      if (error) {
        throw new Error(error.message);
      }

      if (!data.user || !data.session) {
        throw new Error('Failed to sign in');
      }

      setSession(data.session);
      setUser(data.user);

      // Navigate to dashboard
      router.push('/dashboard');
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    setLoading(true);
    try {
      const { error } = await authHelpers.signOut();

      if (error) {
        throw new Error(error.message);
      }

      setSession(null);
      setUser(null);

      // Navigate to login
      router.push('/login');
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
