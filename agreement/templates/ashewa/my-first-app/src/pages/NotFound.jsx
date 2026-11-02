import { Link } from 'react-router-dom';
import '../styles/AuthForm.css';

function NotFound() {
  return (
    <div className="auth-page">
      <div className="auth-container" style={{ gridTemplateColumns: '1fr', maxWidth: '520px', minHeight: 'unset' }}>
        <div className="auth-panel-right" style={{ padding: '56px 40px', textAlign: 'center' }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '72px', fontWeight: 800, color: 'var(--primary-600)', lineHeight: 1 }}>
            404
          </div>
          <h1 className="auth-title" style={{ fontSize: '22px', marginTop: '10px' }}>Page not found</h1>
          <p className="auth-subtitle">The page you're looking for doesn't exist.</p>
          <Link to="/" className="btn-primary" style={{ textDecoration: 'none', display: 'inline-flex', marginTop: '12px' }}>
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}

export default NotFound;
