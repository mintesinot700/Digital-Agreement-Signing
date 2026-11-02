import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { ACCESS_TOKEN, IS_ADMIN, API_ENDPOINTS } from "./constants";
import AgreementForm from "./pages/AgreementForm";
import Login from "./pages/Login";
import Register from "./pages/Register";
import NotFound from "./pages/NotFound";
import AdminDashboard from "./pages/AdminDashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import api from './api';

function clearAuthStorage() {
  localStorage.removeItem(ACCESS_TOKEN);
  localStorage.removeItem(IS_ADMIN);
}

function Logout() {
  const navigate = useNavigate();

  useEffect(() => {
    const performLogout = async () => {
      try {
        await api.post(API_ENDPOINTS.LOGOUT);
        console.log('Successfully logged out from backend.');
      } catch (error) {
        console.error('Logout failed on the backend:', error);
      } finally {
        clearAuthStorage();
        navigate('/login', { replace: true });
      }
    };
    performLogout();
  }, [navigate]);

  return null;
}

function RegisterAndLogout() {
  clearAuthStorage();
  return <Register />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route path="/register" element={<RegisterAndLogout />} />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AgreementForm />
            </ProtectedRoute>
          }
        />

        {/* Admin Dashboard (list + detail merged) */}
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute adminOnly>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* Agreement detail handled inside AdminDashboard */}
        <Route
          path="/agreements/:id"
          element={
            <ProtectedRoute adminOnly>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* PDF Agreements (still handled in AdminDashboard) */}
        <Route
          path="/admin/pdf-agreements"
          element={
            <ProtectedRoute adminOnly>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* Catch-all Route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;