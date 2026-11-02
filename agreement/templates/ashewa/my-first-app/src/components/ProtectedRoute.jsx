import { Navigate, useLocation } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';
import api from '../api';
import { ACCESS_TOKEN, IS_ADMIN } from '../constants';
import { useState, useEffect } from 'react';

function ProtectedRoute({ children, adminOnly = false }) {
  const [authStatus, setAuthStatus] = useState('checking');
  const location = useLocation();

  useEffect(() => {
    const verifyAuth = async () => {
      const token = localStorage.getItem(ACCESS_TOKEN);
      
      // No token, unauthorized.
      if (!token) {
        setAuthStatus('unauthorized');
        return;
      }

      try {
        // Check if token is expired
        const decoded = jwtDecode(token);
        if (decoded.exp < Date.now() / 1000) {
          throw new Error('Token expired');
        }

        // Verify admin status if required
        if (adminOnly) {
          const verifyRes = await api.get('/api/verify-admin/');
          if (!verifyRes.data.is_admin) {
            throw new Error('Admin access required');
          }
          localStorage.setItem(IS_ADMIN, 'true');
        }

        setAuthStatus('authorized');
      } catch (error) {
        console.error('Auth verification failed:', error);
        
        // Let the axios interceptor handle the refresh logic.
        // We only clear localStorage if the interceptor fails.
        localStorage.removeItem(ACCESS_TOKEN);
        localStorage.removeItem(IS_ADMIN);
        setAuthStatus('unauthorized');
      }
    };

    verifyAuth();
  }, [location, adminOnly]);

  if (authStatus === 'checking') {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-2xl text-gray-700">Loading...</div>
    </div>;
  }

  if (authStatus === 'unauthorized') {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

export default ProtectedRoute;