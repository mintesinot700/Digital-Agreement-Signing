import axios from 'axios';
import { ACCESS_TOKEN, IS_ADMIN, API_ENDPOINTS } from './constants';

// API base URL:
// - Local dev: .env sets REACT_APP_API_URL=http://127.0.0.1:8000
// - Production build: .env.production leaves it empty -> the SPA calls the API
//   on its own origin (Django serves both the build and /api/*). The origin
//   must be ABSOLUTE: endpoint strings are relative ("api/..."), so an empty
//   baseURL would resolve them against the current route and turn
//   /admin/dashboard's calls into /admin/api/... which 404s into the SPA.
const baseURL = (
  process.env.REACT_APP_API_URL ||
  (process.env.NODE_ENV === 'production' ? window.location.origin : 'http://127.0.0.1:8000')
).replace(/\/+$/, '');

const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor — attach the access token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(ACCESS_TOKEN);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — store admin flag after login, auto-refresh on 401
api.interceptors.response.use(
  (response) => {
    if (response.config.url.includes(API_ENDPOINTS.LOGIN) && response.data?.is_admin !== undefined) {
      localStorage.setItem(IS_ADMIN, response.data.is_admin ? 'true' : 'false');
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // If 401 (unauthorized), try refreshing the access token.
    // The refresh token lives in an HttpOnly cookie managed by Django,
    // so we just POST with credentials included.
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const url = originalRequest.url || '';

      // A failed login must surface its error in the form — redirecting
      // here reloads the page and wipes the message before it renders.
      if (url.includes(API_ENDPOINTS.LOGIN)) {
        return Promise.reject(error);
      }

      // The refresh call itself failed: the session is truly over.
      // The refresh token lives in an HttpOnly cookie managed by Django,
      // so we just clear local state and send the user to the login page.
      if (url.includes(API_ENDPOINTS.REFRESH)) {
        localStorage.removeItem(ACCESS_TOKEN);
        localStorage.removeItem(IS_ADMIN);
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const res = await axios.post(
          `${baseURL}${API_ENDPOINTS.REFRESH}`,
          {},
          { withCredentials: true }
        );

        if (res.status === 200 && res.data?.access) {
          localStorage.setItem(ACCESS_TOKEN, res.data.access);
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error('Session expired. Please log in again.');
        localStorage.removeItem(ACCESS_TOKEN);
        localStorage.removeItem(IS_ADMIN);
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Authenticated file download helper (e.g. agreement summary PDFs)
export async function downloadAuthedFile(url, filename) {
  const token = localStorage.getItem(ACCESS_TOKEN);
  const response = await fetch(`${baseURL}${url}`.replace(/([^:]\/)\/+/g, '$1'), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error(`Download failed (${response.status})`);
  }
  const blob = await response.blob();
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}

export default api;
