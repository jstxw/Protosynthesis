'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Lock, User, Eye, EyeOff, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

/**
 * Sign Up Page Component
 *
 * Features:
 * - Username/password registration via Supabase
 * - Social signup options (Google, GitHub)
 * - Password visibility toggle
 * - Form validation
 * - Responsive split-screen design
 */
export function SignUp() {
    const { signUp } = useAuth();
    const [formData, setFormData] = useState({
        username: '',
        password: '',
    });
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Validation
        if (formData.username.length < 3) {
            setError('Username must be at least 3 characters');
            return;
        }

        if (formData.password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        setIsLoading(true);

        try {
            // Generate email from username for Supabase (internal use only)
            const generatedEmail = `${formData.username}@nodelink.app`;
            await signUp(generatedEmail, formData.password, formData.username);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create account. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSocialSignup = (provider: 'google' | 'github') => {
        console.log(`Sign up with ${provider}`);
        // TODO: Implement social signup with Supabase
    };

    const updateFormData = (field: string, value: string) => {
        setFormData({ ...formData, [field]: value });
    };

    return (
        <div className="min-h-screen bg-black flex">
            {/* Left Side - Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center px-8 py-12">
                <div className="w-full max-w-md">
                    {/* Logo */}
                    <div className="mb-8">
                        <img
                            src="/icons/logo.svg"
                            alt="Logo"
                            className="w-16 h-16 mb-6"
                        />
                        <h1 className="text-hero text-text-primary mb-2">Create account</h1>
                        <p className="text-body text-text-secondary">
                            Start building powerful API workflows today.
                        </p>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 bg-status-error/10 border border-status-error/20 rounded-lg flex items-center gap-3">
                            <AlertCircle className="w-5 h-5 text-status-error flex-shrink-0" />
                            <p className="text-small text-status-error">{error}</p>
                        </div>
                    )}

                    {/* Social Signup */}
                    <div className="space-y-3 mb-6">
                        <button
                            onClick={() => handleSocialSignup('google')}
                            className="btn-secondary w-full justify-center"
                        >
                            <img src="/icons/google.svg" alt="Google" className="w-5 h-5" />
                            <span>Continue with Google</span>
                        </button>
                        <button
                            onClick={() => handleSocialSignup('github')}
                            className="btn-secondary w-full justify-center"
                        >
                            <img src="/icons/github.svg" alt="GitHub" className="w-5 h-5" />
                            <span>Continue with GitHub</span>
                        </button>
                    </div>

                    {/* Divider */}
                    <div className="relative mb-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-border"></div>
                        </div>
                        <div className="relative flex justify-center text-small">
                            <span className="px-4 bg-black text-text-tertiary">Or create an account</span>
                        </div>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Username */}
                        <div>
                            <label htmlFor="username" className="form-label">
                                Username
                            </label>
                            <div className="input-with-icon">
                                <User className="input-icon-left w-5 h-5" />
                                <input
                                    id="username"
                                    type="text"
                                    value={formData.username}
                                    onChange={(e) => updateFormData('username', e.target.value)}
                                    placeholder="johndoe"
                                    className="form-input"
                                    required
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div>
                            <label htmlFor="password" className="form-label">
                                Password
                            </label>
                            <div className="input-with-icon input-with-icon-right">
                                <Lock className="input-icon-left w-5 h-5" />
                                <input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    value={formData.password}
                                    onChange={(e) => updateFormData('password', e.target.value)}
                                    placeholder="••••••••"
                                    className="form-input"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="input-icon-right hover:text-text-primary transition-colors cursor-pointer"
                                    style={{ pointerEvents: 'auto' }}
                                >
                                    {showPassword ? (
                                        <EyeOff className="w-5 h-5" />
                                    ) : (
                                        <Eye className="w-5 h-5" />
                                    )}
                                </button>
                            </div>

                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="btn-primary w-full justify-center"
                        >
                            {isLoading ? 'Creating account...' : 'Create account'}
                        </button>
                    </form>

                    {/* Login Link */}
                    <p className="mt-6 text-center text-small text-text-secondary">
                        Already have an account?{' '}
                        <Link
                            href="/login"
                            className="text-accent-blue hover:text-accent-blue-hover font-medium transition-colors"
                        >
                            Sign in
                        </Link>
                    </p>
                </div>
            </div>

            {/* Right Side - Hero Image */}
            <div className="hidden lg:flex lg:w-1/2 bg-app-panel items-center justify-center p-12">
                <div className="max-w-lg text-center">
                    <img
                        src="/icons/hero-illustration.svg"
                        alt="API Workflow"
                        className="w-full mb-8 opacity-90"
                    />
                    <h2 className="text-heading text-text-primary mb-4">
                        Join thousands of developers
                    </h2>
                    <p className="text-body text-text-secondary mb-6">
                        Build, test, and deploy API workflows faster than ever. No infrastructure management needed.
                    </p>
                    <div className="flex items-center justify-center gap-4 text-small text-text-tertiary">
                        <div className="flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4 text-status-success" />
                            <span>Free to start</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4 text-status-success" />
                            <span>No credit card</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SignUp;
