// Authentication Tokens (keeping your original structure)
export const TOKENS = {
  ACCESS: "access",
  REFRESH: "refresh"
};

// Admin Constants (new additions)
export const ADMIN = {
  ROLE: "is_admin",
  DASHBOARD_PATH: "/admin/dashboard"
};

// Maintain your original exports
export const ACCESS_TOKEN = TOKENS.ACCESS;
export const REFRESH_TOKEN = TOKENS.REFRESH;
export const IS_ADMIN = ADMIN.ROLE;

// API Endpoints (optional but recommended)
export const API_ENDPOINTS = {
  LOGIN: "api/token/",
  REFRESH: "api/token/refresh/",
  VERIFY_ADMIN: "api/verify-admin/"
};