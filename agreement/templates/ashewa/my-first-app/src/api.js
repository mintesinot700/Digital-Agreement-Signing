import axios from 'axios';
import { ACCESS_TOKEN, IS_ADMIN, API_ENDPOINTS } from './constants';

const DEFAULT_API_URL = 'http://127.0.0.1:8000/';
const baseURL = process.env.REACT_APP_API_URL || DEFAULT_API_URL;

const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor
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

// Response interceptor
api.interceptors.response.use(
  (response) => {
    if (response.config.url.includes(API_ENDPOINTS.LOGIN) && response.data?.is_admin !== undefined) {
      localStorage.setItem(IS_ADMIN, response.data.is_admin ? 'true' : 'false');
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // If 401 (unauthorized), try refreshing access token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      console.log('api.js: Attempting to refresh token due to 401');

      try {
        // No refresh token in localStorage anymore – Django handles it via cookie
        const res = await axios.post(
          `${baseURL}${API_ENDPOINTS.REFRESH}`,
          {}, // empty body, DRF will read refresh token from cookie
          { withCredentials: true }
        );

        if (res.status === 200) {
          localStorage.setItem(ACCESS_TOKEN, res.data.access);
          console.log('api.js: Token refresh successful');
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error('api.js: Token refresh failed:', refreshError.response?.data || refreshError.message);
        localStorage.removeItem(ACCESS_TOKEN);
        localStorage.removeItem(IS_ADMIN);
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }

    console.error('api.js: Request failed:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default api;