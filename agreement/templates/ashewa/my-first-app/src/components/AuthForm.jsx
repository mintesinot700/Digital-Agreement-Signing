import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { ACCESS_TOKEN, REFRESH_TOKEN, IS_ADMIN } from '../constants';
import '../styles/AuthForm.css';
import LoadingIndicator from './LoadingIndicator';

// The 'onLogin' prop is now a required part of this component
function AuthForm({ route, method, onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [phone_number, setPhone_number] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const name = method === 'login' ? 'Login' : 'Register';

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
      console.log(`AuthForm: Sending ${method} request to ${route}`, { payload });
      const res = await api.post(route, payload);
      console.log('AuthForm: Login response', {
        status: res.status,
        data: res.data,
        is_admin: res.data.is_admin
      });
      localStorage.setItem(ACCESS_TOKEN, res.data.access);
      // NOTE: Storing the refresh token in localStorage is generally not recommended
      // for security reasons. It's often better to rely on an HttpOnly cookie.
      // This line is kept as per the user's request not to remove code.
      localStorage.setItem(REFRESH_TOKEN, res.data.refresh);

      if (method === 'login') {
        console.log('AuthForm: Verifying admin status via /verify-admin/');
        try {
          const verifyRes = await api.get('api/verify-admin/', {
            headers: { Authorization: `Bearer ${res.data.access}` }
          });
          console.log('AuthForm: Admin verification response', {
            status: verifyRes.status,
            data: verifyRes.data,
            is_admin: verifyRes.data.is_admin
          });
          const isAdmin = verifyRes.data.is_admin === true || verifyRes.data.is_admin === 'true';
          localStorage.setItem(IS_ADMIN, isAdmin ? 'true' : 'false');
          console.log(`AuthForm: isAdmin evaluated to ${isAdmin}`);

          // CRITICAL: Call the onLogin function to update the parent state
          if (onLogin) {
            onLogin();
          }

          if (isAdmin) {
            console.log('AuthForm: User is admin, redirecting to /admin/dashboard');
            navigate('/admin/dashboard');
          } else {
            console.log('AuthForm: User is not admin, redirecting to /');
            navigate('/');
          }
        } catch (verifyError) {
          console.error('AuthForm: Admin verification failed', {
            status: verifyError.response?.status,
            data: verifyError.response?.data,
            message: verifyError.message
          });
          setError('Failed to verify admin status. Redirecting to home.');
          // Delay navigation to allow error to render and display briefly
          setTimeout(() => {
            navigate('/');
          }, 2000); // 2 seconds - adjust as needed for visibility
        }
      } else {
        console.log('AuthForm: Redirecting to /login after registration');
        navigate('/login');
      }
    } catch (error) {
      console.error(`AuthForm: ${method} error`, {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      });
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else if (error.response?.data) {
        let errorMessages = [];
        for (const key in error.response.data) {
          errorMessages.push(`${key}: ${error.response.data[key].join(', ')}`);
        }
        setError(errorMessages.join('\n'));
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setLoading(false); // No delay needed - set immediately for better UX
    }
  };

  return (
    <div className="auth-container">
      {method === 'register' && (
        <div className="auth-panel-left">
          <div className="logo-placeholder">
            <h1 className="logo logoone">
              <a href="/">
                {process.env.NODE_ENV === 'development' ? (
                  <img
                    src={require('../logo/images.png')}
                    alt="Ashewa Technology Logo"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                ) : (
                  <img
                    src="/static/logo/images.png"
                    alt="Ashewa Technology Logo"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
              </a>
            </h1>
          </div>
          <h2>Welcome Back!</h2>
          <p>To keep connected with us please login with your personal info</p>
          <button className="panel-button" onClick={() => navigate('/login')}>
            SIGN IN
          </button>
        </div>
      )}

      <div className="auth-panel-right">
        <h1>{method === 'login' ? 'Login' : 'Create Account'}</h1>
        <form onSubmit={handleSubmit} className="form-container">
          {error && <div className="error-message">{error}</div>}
          <div className="input-group">
            <label htmlFor="username-input" className="input-label">Name</label>
            <span className="input-icon">👤</span>
            <input
              className="form-input"
              id="username-input"
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your name"
            />
          </div>
          {method === 'register' && (
            <div className="email-phone-section">
              <div className="input-group">
                <label htmlFor="email-input" className="input-label">Email</label>
                <span className="input-icon">📧</span>
                <input
                  className="form-input"
                  required
                  id="email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                />
              </div>
              <div className="input-group">
                <label htmlFor="phone-input" className="input-label">Phone</label>
                <span className="input-icon">📞</span>
                <input
                  className="form-input"
                  id="phone-input"
                  type="text"
                  required
                  value={phone_number}
                  onChange={(e) => setPhone_number(e.target.value)}
                  placeholder="Enter your phone number"
                />
              </div>
            </div>
          )}
          <div className="input-group">
            <label htmlFor="password-input" className="input-label">Password</label>
            <span className="input-icon">🔒</span>
            <input
              required
              className="form-input"
              id="password-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />
          </div>
          {loading && <LoadingIndicator />}
          <button className="form-button" type="submit">
            {method === 'login' ? 'SIGN IN' : 'SIGN UP'}
          </button>
        </form>
      </div>

      {method === 'login' && (
        <div className="auth-panel-left">
          <div className="logo-placeholder">
            <h1 className="logo logoone">
              <a href="/">
                {process.env.NODE_ENV === 'development' ? (
                  <img
                    src={require('../logo/images.png')}
                    alt="Ashewa Technology Logo"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                ) : (
                  <img
                    src="/static/logo/images.png"
                    alt="Ashewa Technology Logo"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
              </a>
            </h1>
          </div>
          <h2>Hello Partner!</h2>
          <p>Enter your personal details and start your journey with us</p>
          <button className="panel-button" onClick={() => navigate('/register')}>
            SIGN UP
          </button>
        </div>
      )}
    </div>
  );
}

export default AuthForm;