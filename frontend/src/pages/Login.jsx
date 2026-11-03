import AuthForm from '../components/AuthForm';

function Login() {
  const handleLogin = () => {
    // Auth state lives in localStorage; AuthForm navigates after verifying.
  };

  return <AuthForm route="/api/token/" method="login" onLogin={handleLogin} />;
}

export default Login;
