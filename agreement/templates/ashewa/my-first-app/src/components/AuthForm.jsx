import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaUser, FaEnvelope, FaPhone, FaLock, FaEye, FaEyeSlash, FaPenNib, FaShieldAlt, FaBolt, FaFileSignature, FaCheck } from 'react-icons/fa';
import api from '../api';
import { ACCESS_TOKEN, REFRESH_TOKEN, IS_ADMIN } from '../constants';
import '../styles/AuthForm.css';
import LoadingIndicator from './LoadingIndicator';

const FEATURES = [
  { icon: FaPenNib, title: 'Draw your signature', text: 'Sign on any device with mouse or touch.' },
  { icon: FaFileSignature, title: 'Ready-made templates', text: 'Pick an agreement PDF and fill it in minutes.' },
  { icon: FaShieldAlt, title: 'Secure & audited', text: 'JWT auth, token blacklisting and a full audit trail.' },
  { icon: FaBolt, title: 'Instant status updates', text: 'Email notifications the moment your agreement is reviewed.' },
];

function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 64 64" aria-hidden="true">
      <rect width="64" height="64" rx="16" fill="rgba(255,255,255,0.14)" />
      <path
        d="M14 42c6-2 10-14 16-14s5 10 10 10c4 0 6-4 10-6"
        stroke="#fff"
        strokeWidth="4.5"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  );
}

// The 'onLogin' prop is a required part of this component
function AuthForm({ route, method, onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [phone_number, setPhone_number] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let payload = { username, password };
      if (method === 'register') {
        payload.email = email;
        payload.phone_number = phone_number;
      }
      const res = await api.post(route, payload);
      localStorage.setItem(ACCESS_TOKEN, res.data.access);
      localStorage.setItem(REFRESH_TOKEN, res.data.refresh);

      if (method === 'login') {
        try {
          const verifyRes = await api.get('api/verify-admin/', {
            headers: { Authorization: `Bearer ${res.data.access}` },
          });
          const isAdmin = verifyRes.data.is_admin === true || verifyRes.data.is_admin === 'true';
          localStorage.setItem(IS_ADMIN, isAdmin ? 'true' : 'false');

          if (onLogin) {
            onLogin();
          }

          navigate(isAdmin ? '/admin/dashboard' : '/');
        } catch (verifyError) {
          console.error('AuthForm: Admin verification failed', verifyError.response?.status);
          setError('Failed to verify admin status. Redirecting to home.');
          setTimeout(() => {
            navigate('/');
          }, 2000);
        }
      } else {
        navigate('/login');
      }
    } catch (error) {
      if (error.code === 'ECONNABORTED') {
        setError('The server took too long to respond — on the free tier it sleeps and needs a minute to wake up. Please try again.');
      } else if (!error.response) {
        setError('Cannot reach the server. Check your connection and try again.');
      } else if (error.response.status >= 500) {
        setError(`Server error (${error.response.status}) — please try again in a moment.`);
      } else {
        const data = error.response.data;
        if (typeof data?.detail === 'string') {
          setError(data.detail);
        } else if (typeof data?.error === 'string') {
          setError(data.error);
        } else if (data && typeof data === 'object' && !Array.isArray(data)) {
          const errorMessages = Object.entries(data).map(
            ([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`
          );
          setError(errorMessages.join('\n') || 'Request failed. Please try again.');
        } else {
          setError('An error occurred. Please try again.');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* Brand / marketing panel */}
        <div className="auth-panel-left">
          <div className="brand-header">
            <BrandMark />
            <div className="brand-text">
              <span className="brand-name">SignFlow</span>
              <span className="brand-tagline">by Ashewa Technology</span>
            </div>
          </div>

          <div className="brand-body">
            <h1 className="brand-headline">
              Digital agreements,<br />signed in seconds.
            </h1>
            <p className="brand-sub">
              Upload, review and e-sign contracts with a legally binding
              handwritten signature — from anywhere, on any device.
            </p>

            <ul className="brand-features">
              {FEATURES.map(({ icon: Icon, title, text }) => (
                <li key={title} className="brand-feature">
                  <span className="brand-feature-icon"><Icon /></span>
                  <span className="brand-feature-copy">
                    <strong>{title}</strong>
                    <small>{text}</small>
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="brand-footer">
            <span className="brand-stat"><FaCheck /> Audit trail on every action</span>
            <span className="brand-stat"><FaCheck /> Encrypted file storage</span>
          </div>
        </div>

        {/* Form panel */}
        <div className="auth-panel-right">
          <div className="auth-card">
            <h1 className="auth-title">
              {method === 'login' ? 'Welcome back' : 'Create your account'}
            </h1>
            <p className="auth-subtitle">
              {method === 'login'
                ? 'Sign in to submit and follow your agreements.'
                : 'Register once — then sign agreements in a couple of clicks.'}
            </p>

            <form onSubmit={handleSubmit} className="form-container">
              {error && (
                <div className="error-message" role="alert">
                  {error.split('\n').map((line, i) => <div key={i}>{line}</div>)}
                </div>
              )}

              <div className="input-group">
                <label htmlFor="username-input" className="input-label">Username</label>
                <div className="input-wrap">
                  <span className="input-icon"><FaUser /></span>
                  <input
                    className="form-input"
                    id="username-input"
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter your username"
                    autoComplete="username"
                  />
                </div>
              </div>

              {method === 'register' && (
                <div className="email-phone-section">
                  <div className="input-group">
                    <label htmlFor="email-input" className="input-label">Email</label>
                    <div className="input-wrap">
                      <span className="input-icon"><FaEnvelope /></span>
                      <input
                        className="form-input"
                        required
                        id="email-input"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        autoComplete="email"
                      />
                    </div>
                  </div>
                  <div className="input-group">
                    <label htmlFor="phone-input" className="input-label">Phone</label>
                    <div className="input-wrap">
                      <span className="input-icon"><FaPhone /></span>
                      <input
                        className="form-input"
                        id="phone-input"
                        type="tel"
                        required
                        value={phone_number}
                        onChange={(e) => setPhone_number(e.target.value)}
                        placeholder="+251 911 234 567"
                        autoComplete="tel"
                      />
                    </div>
                  </div>
                </div>
              )}

              <div className="input-group">
                <label htmlFor="password-input" className="input-label">Password</label>
                <div className="input-wrap">
                  <span className="input-icon"><FaLock /></span>
                  <input
                    required
                    className="form-input"
                    id="password-input"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    autoComplete={method === 'login' ? 'current-password' : 'new-password'}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <FaEyeSlash /> : <FaEye />}
                  </button>
                </div>
              </div>

              {loading && <LoadingIndicator />}

              <button className="form-button" type="submit" disabled={loading}>
                {loading ? 'Please wait…' : method === 'login' ? 'Sign in' : 'Create account'}
              </button>
            </form>

            <div className="auth-switch">
              {method === 'login' ? (
                <>New here? <button type="button" className="link-btn" onClick={() => navigate('/register')}>Create an account</button></>
              ) : (
                <>Already have an account? <button type="button" className="link-btn" onClick={() => navigate('/login')}>Sign in</button></>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthForm;
