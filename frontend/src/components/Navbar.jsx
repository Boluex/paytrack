import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? 'nav-link active' : 'nav-link';

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <div className="brand-icon">💳</div>
        PayTrack
      </Link>

      <div className="navbar-nav">
        <Link to="/" className={isActive('/')}>Dashboard</Link>
        <Link to="/transactions" className={isActive('/transactions')}>Transactions</Link>
      </div>

      <div className="navbar-actions">
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          {user?.business_name}
        </span>
        <button className="btn btn-ghost" onClick={logout}>Logout</button>
      </div>
    </nav>
  );
}
