'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Eye, EyeOff, AlertCircle, Key, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import '../auth.css';

/**
 * Signup Page Component
 *
 * Features:
 * - Email/password registration via Supabase
 * - Optional username/display name
 * - Social login options (Google, GitHub)
 * - Password visibility toggle
 * - Password confirmation with validation
 * - Error handling
 * - Node-based visual design
 */
export function SignUp() {
    const { signUp } = useAuth();
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            setError('Please enter a valid email address.');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters long.');
            return;
        }

        setIsLoading(true);

        try {
            await signUp(email, password, username || undefined);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create an account. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSocialLogin = (provider: 'google' | 'github') => {
        console.log(`Sign up with ${provider}`);
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

                        {/* Username Port (Optional) */}
                        <div className="auth-port output">
                            <div className="auth-port-content">
                                <label htmlFor="username">Username (Optional)</label>
                                <input
                                    id="username"
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder="Choose a display name"
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
                                        placeholder="Create a password"
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

                        {/* Confirm Password Port */}
                        <div className="auth-port output">
                            <div className="auth-port-content">
                                <label htmlFor="confirm-password">Confirm Password</label>
                                <div className="password-input-wrapper">
                                    <input
                                        id="confirm-password"
                                        type={showConfirmPassword ? 'text' : 'password'}
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        placeholder="Confirm your password"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        className="password-toggle"
                                    >
                                        {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
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
                    {/* Email line */}
                    <line className="auth-connector-line" x1="280" y1="90" x2="320" y2="90" />
                    {/* Username line */}
                    <line className="auth-connector-line" x1="280" y1="130" x2="320" y2="130" />
                    {/* Password line */}
                    <line className="auth-connector-line" x1="280" y1="170" x2="320" y2="170" />
                    {/* Confirm Password line */}
                    <line className="auth-connector-line" x1="280" y1="210" x2="320" y2="210" />
                </svg>

                {/* Create Account Node (Right) */}
                <form onSubmit={handleSubmit} style={{ position: 'relative', zIndex: 1 }}>
                    <div className="auth-node main-auth-node">
                        <div className="node-icon-nub node-header-signup">
                            <Key className="node-nub-icon" size={22} />
                        </div>
                        <header className="node-header node-header-signup">
                            <h1>Create Account</h1>
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

                            {/* Username Input Port */}
                            <div className="auth-port input">
                                <div className="auth-port-handle connected"></div>
                                <div className="auth-port-content">
                                    <div className="auth-port-label">
                                        <span>Username</span>
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

                            {/* Confirm Password Input Port */}
                            <div className="auth-port input">
                                <div className="auth-port-handle connected"></div>
                                <div className="auth-port-content">
                                    <div className="auth-port-label">
                                        <span>Confirm Password</span>
                                        <span className="port-type">(string)</span>
                                    </div>
                                </div>
                            </div>

                            {/* Submit Button Port */}
                            <div className="auth-port output">
                                <div className="auth-port-content">
                                    <button type="submit" disabled={isLoading} className="auth-button">
                                        {isLoading ? 'Creating Account...' : 'Sign Up'}
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
                                Already have an account?{' '}
                                <Link href="/login">
                                    Sign in
                                </Link>
                            </p>
                        </footer>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default SignUp;