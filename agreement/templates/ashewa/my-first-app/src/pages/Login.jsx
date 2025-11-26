import React, { useState } from 'react';
import AuthForm from '../components/AuthForm';
import '../styles/AuthForm.css';

function Login() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const handleLogin = () => {
        setIsAuthenticated(true); // Update state if needed
    };

    return (
        <div className="auth-container">
            <AuthForm route="/api/token/" method="login" onLogin={handleLogin} />
        </div>
    );
}

export default Login;