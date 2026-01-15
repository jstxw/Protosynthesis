'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Eye, EyeOff, AlertCircle, Key, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import '../auth.css'

/**
 * Login Page Component
 *
 * Features:
 * - Email/password authentication via Supabase
 * - Social login options (Google, GitHub)
 * - Password visibility toggle
 * - Error handling
 * - Node-based visual design
 */
export function Login() {
    const { signIn } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await signIn(email, password);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to sign in. Please check your credentials.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSocialLogin = (provider: 'google' | 'github') => {
        console.log(`Login with ${provider}`);
        // TODO: Implement social login with Supabase
    };

    return (
        <div className="auth-page">
            <div className="auth-nodes-container" style={{ position: 'relative' }}>
                {/* User Info Node (Left) */}
                <div className="auth-node user-info-node" style={{ position: 'relative', zIndex: 1 }}>
                    <div className="node-icon-nub node-header-userinfo">
                        <User className="node-nub-icon" size={22} />
                    </div>
                    <header className="node-header node-header-userinfo">
                        <h1>User Info</h1>
                        <span className="node-type">INFO</span>
                    </header>

                    <main className="auth-body">
                        {/* Email Port */}
                        <div className="auth-port output">
                            <div className="auth-port-content">
                                <label htmlFor="email">Email</label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="your.email@example.com"
                                    required
                                />
                            </div>
                            <div className="auth-port-handle connected"></div>
                        </div>

                        {/* Password Port */}
                        <div className="auth-port output">
                            <div className="auth-port-content">
                                <label htmlFor="password">Password</label>
                                <div className="password-input-wrapper">
                                    <input
                                        id="password"
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="••••••••"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="password-toggle"
                                    >
                                        {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                    </button>
                                </div>
                            </div>
                            <div className="auth-port-handle connected"></div>
                        </div>
                    </main>
                </div>

                {/* Animated Connector Lines */}
                <svg className="auth-connector-svg" style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    pointerEvents: 'none',
                    zIndex: 0
                }}>
                    {/* Email line - header(36) + margin-top(30) + body-padding(10) + first-port-middle(~20) */}
                    <line className="auth-connector-line" x1="280" y1="96" x2="320" y2="96" />
                    {/* Password line - email + port-height(~40) */}
                    <line className="auth-connector-line" x1="280" y1="136" x2="320" y2="136" />
                </svg>

                {/* Sign In Node (Right) */}
                <form onSubmit={handleSubmit} style={{ position: 'relative', zIndex: 1 }}>
                    <div className="auth-node main-auth-node">
                        <div className="node-icon-nub node-header-login">
                            <Key className="node-nub-icon" size={22} />
                        </div>
                        <header className="node-header node-header-login">
                            <h1>Sign In</h1>
                            <span className="node-type">AUTH</span>
                        </header>

                        {error && (
                            <div className="auth-error">
                                <AlertCircle size={16} />
                                <span>{error}</span>
                            </div>
                        )}

                        <main className="auth-body">
                            {/* Email Input Port */}
                            <div className="auth-port input">
                                <div className="auth-port-handle connected"></div>
                                <div className="auth-port-content">
                                    <div className="auth-port-label">
                                        <span>Email</span>
                                        <span className="port-type">(string)</span>
                                    </div>
                                </div>
                            </div>

                            {/* Password Input Port */}
                            <div className="auth-port input">
                                <div className="auth-port-handle connected"></div>
                                <div className="auth-port-content">
                                    <div className="auth-port-label">
                                        <span>Password</span>
                                        <span className="port-type">(string)</span>
                                    </div>
                                </div>
                            </div>

                            {/* Submit Button Port */}
                            <div className="auth-port output">
                                <div className="auth-port-content">
                                    <button type="submit" disabled={isLoading} className="auth-button">
                                        {isLoading ? 'Signing in...' : 'Sign In'}
                                    </button>
                                </div>
                                <div className="auth-port-handle"></div>
                            </div>
                        </main>

                        <footer className="auth-footer">
                            <div className="auth-divider">Or</div>
                            <div className="social-buttons">
                                <button type="button" onClick={() => handleSocialLogin('google')} className="social-button">
                                    <svg viewBox="0 0 24 24" width="18" height="18">
                                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                                    </svg>
                                    <span>Continue with Google</span>
                                </button>
                            </div>
                            <p className="auth-link">
                                Don't have an account?{' '}
                                <Link href="/signup">
                                    Sign up
                                </Link>
                            </p>
                        </footer>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default Login;
