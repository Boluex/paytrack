import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [businessName, setBusinessName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const { register, user } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(email, password, businessName);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  // After registration, show API key
  if (user && !apiKey && user.api_key) {
    setApiKey(user.api_key);
  }

  if (apiKey) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="brand-row">
            <div className="brand-icon">💳</div>
            <span>PayTrack</span>
          </div>
          <h1>You're all set! 🎉</h1>
          <p className="subtitle">Your merchant account has been created. Save your API key — you'll need it to log transactions.</p>

          <div className="form-group">
            <label className="form-label">Your API Key</label>
            <div className="api-key-display">
              <span>{apiKey}</span>
              <button className="copy-btn" onClick={() => navigator.clipboard.writeText(apiKey)}>
                Copy
              </button>
            </div>
          </div>

          <div className="alert alert-success">
            ⚠️ Store this key securely. You can also find it in your dashboard settings.
          </div>

          <button className="btn btn-primary btn-block btn-lg" onClick={() => navigate('/')}>
            Go to Dashboard →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="brand-row">
          <div className="brand-icon">💳</div>
          <span>PayTrack</span>
        </div>

        <h1>Create account</h1>
        <p className="subtitle">Start monitoring your payment transactions</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="businessName">Business Name</label>
            <input
              id="businessName"
              className="form-input"
              type="text"
              placeholder="Acme Payments Inc."
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="email">Email</label>
            <input
              id="email"
              className="form-input"
              type="email"
              placeholder="merchant@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              className="form-input"
              type="password"
              placeholder="Minimum 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>

          <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={loading}>
            {loading ? <div className="spinner" /> : 'Create Account'}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
