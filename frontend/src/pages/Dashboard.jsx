import { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import StatsCard from '../components/StatsCard';
import TransactionTable from '../components/TransactionTable';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, txnRes] = await Promise.all([
        client.get('/transactions/stats'),
        client.get('/transactions?page_size=10'),
      ]);
      setStats(statsRes.data);
      setRecent(txnRes.data.transactions);
    } catch (err) {
      console.error('Failed to fetch dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (val) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `$${(val / 1000).toFixed(1)}K`;
    return `$${val.toFixed(2)}`;
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)', padding: '0.75rem 1rem',
          fontSize: '0.85rem',
        }}>
          <p style={{ color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{label}</p>
          <p style={{ color: 'var(--primary-light)', fontWeight: 600 }}>
            {payload[0].value} transactions
          </p>
          {payload[1] && (
            <p style={{ color: 'var(--accent)', fontWeight: 600 }}>
              ${Number(payload[1].value).toFixed(2)}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="app-layout">
        <Navbar />
        <div className="loading-container"><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="app-layout">
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <h1>Dashboard</h1>
          <p>Welcome back, {user?.business_name}</p>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid">
          <StatsCard
            icon="📊"
            value={stats?.total_transactions || 0}
            label="Total Transactions"
            variant="primary"
          />
          <StatsCard
            icon="💰"
            value={formatCurrency(stats?.total_volume || 0)}
            label="Total Volume"
            variant="success"
          />
          <StatsCard
            icon="✅"
            value={`${stats?.success_rate || 0}%`}
            label="Success Rate"
            variant="success"
          />
          <StatsCard
            icon="🚩"
            value={stats?.flagged_count || 0}
            label="Flagged"
            variant="danger"
          />
        </div>

        {/* Chart */}
        {stats?.daily_volume && stats.daily_volume.length > 0 && (
          <div className="chart-container">
            <h3>Transaction Volume — Last 7 Days</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={stats.daily_volume}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} />
                <YAxis stroke="var(--text-muted)" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="count" stroke="#6366f1" fillOpacity={1} fill="url(#colorCount)" strokeWidth={2} />
                <Area type="monotone" dataKey="volume" stroke="#22d3ee" fillOpacity={1} fill="url(#colorVolume)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* API Key */}
        <div className="card" style={{ marginBottom: 'var(--space-2xl)' }}>
          <h3 style={{ marginBottom: 'var(--space-md)', fontSize: '1rem' }}>Your API Key</h3>
          <div className="api-key-display">
            <span>{user?.api_key}</span>
            <button className="copy-btn" onClick={() => navigator.clipboard.writeText(user?.api_key)}>
              Copy
            </button>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="table-container">
          <div className="table-header">
            <h3>Recent Transactions</h3>
          </div>
          <TransactionTable transactions={recent} compact />
        </div>
      </div>
    </div>
  );
}
