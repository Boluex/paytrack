import { useState, useEffect } from 'react';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';

export default function Settings() {
  const { user, refreshUser } = useAuth();
  const [webhookUrl, setWebhookUrl] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [copied, setCopied] = useState(false);
  const [loadingWebhook, setLoadingWebhook] = useState(false);
  const [loadingKey, setLoadingKey] = useState(false);
  const [webhookMessage, setWebhookMessage] = useState({ type: '', text: '' });
  const [keyMessage, setKeyMessage] = useState({ type: '', text: '' });
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  useEffect(() => {
    fetchWebhook();
  }, []);

  const fetchWebhook = async () => {
    try {
      const res = await client.get('/webhooks');
      setWebhookUrl(res.data.webhook_url || '');
    } catch (err) {
      console.error('Failed to fetch webhook config', err);
    }
  };

  const handleSaveWebhook = async (e) => {
    e.preventDefault();
    setWebhookMessage({ type: '', text: '' });
    setLoadingWebhook(true);
    try {
      const res = await client.put('/webhooks', { webhook_url: webhookUrl });
      setWebhookMessage({ type: 'success', text: res.data.message || 'Webhook URL updated.' });
      await refreshUser();
    } catch (err) {
      setWebhookMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to update webhook URL.',
      });
    } finally {
      setLoadingWebhook(false);
    }
  };

  const handleDeleteWebhook = async () => {
    setWebhookMessage({ type: '', text: '' });
    setLoadingWebhook(true);
    try {
      const res = await client.delete('/webhooks');
      setWebhookUrl('');
      setWebhookMessage({ type: 'success', text: res.data.message || 'Webhook URL removed.' });
      await refreshUser();
    } catch (err) {
      setWebhookMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to remove webhook URL.',
      });
    } finally {
      setLoadingWebhook(false);
    }
  };

  const handleCopyKey = () => {
    if (user?.api_key) {
      navigator.clipboard.writeText(user.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRegenerateKey = async () => {
    setKeyMessage({ type: '', text: '' });
    setLoadingKey(true);
    setShowConfirmModal(false);
    try {
      await client.post('/auth/regenerate-api-key');
      setKeyMessage({ type: 'success', text: 'API Key regenerated successfully. Update any external integrations.' });
      await refreshUser();
    } catch (err) {
      setKeyMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to regenerate API Key.',
      });
    } finally {
      setLoadingKey(false);
    }
  };

  const maskKey = (key) => {
    if (!key) return '';
    return `${key.slice(0, 5)}${'•'.repeat(24)}${key.slice(-4)}`;
  };

  return (
    <div className="app-layout">
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <h1>Settings</h1>
          <p>Manage your API keys, webhook integrations, and account configuration</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--space-xl)' }}>
          {/* API Key Management */}
          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-sm)', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              🔑 API Integration Key
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 'var(--space-lg)' }}>
              Use this key to authenticate transaction log requests from your servers. Do not share it.
            </p>

            {keyMessage.text && (
              <div className={`alert alert-${keyMessage.type}`}>
                {keyMessage.text}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Active API Key</label>
              <div className="api-key-display" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontFamily: 'monospace', letterSpacing: '1px' }}>
                  {showApiKey ? user?.api_key : maskKey(user?.api_key)}
                </span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="copy-btn" onClick={() => setShowApiKey(!showApiKey)}>
                    {showApiKey ? 'Hide' : 'Show'}
                  </button>
                  <button className="copy-btn" onClick={handleCopyKey}>
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
              </div>
            </div>

            <div style={{ marginTop: 'var(--space-lg)', borderTop: '1px solid var(--border)', paddingTop: 'var(--space-lg)' }}>
              <button
                className="btn btn-secondary"
                style={{ borderColor: 'var(--danger)', color: '#f87171' }}
                onClick={() => setShowConfirmModal(true)}
                disabled={loadingKey}
              >
                {loadingKey ? 'Regenerating...' : 'Regenerate API Key'}
              </button>
            </div>
          </div>

          {/* Webhook Configuration */}
          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-sm)', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              🪝 Webhook Integration
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 'var(--space-lg)' }}>
              Configure a destination URL to receive real-time HTTP POST notifications whenever a new transaction is logged.
            </p>

            {webhookMessage.text && (
              <div className={`alert alert-${webhookMessage.type}`}>
                {webhookMessage.text}
              </div>
            )}

            <form onSubmit={handleSaveWebhook}>
              <div className="form-group">
                <label className="form-label" htmlFor="webhookUrl">Webhook Target URL</label>
                <input
                  id="webhookUrl"
                  type="url"
                  className="form-input"
                  placeholder="https://yourserver.com/webhooks/paytrack"
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                <button type="submit" className="btn btn-primary" disabled={loadingWebhook}>
                  {loadingWebhook ? 'Saving...' : 'Save Webhook URL'}
                </button>
                {user?.webhook_url && (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ borderColor: 'var(--danger)', color: '#f87171' }}
                    onClick={handleDeleteWebhook}
                    disabled={loadingWebhook}
                  >
                    Remove Webhook
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '1rem'
        }}>
          <div className="card-glass" style={{ maxWidth: '480px', width: '100%', border: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: 'var(--space-sm)' }}>⚠️ Regenerate API Key?</h3>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: 'var(--space-lg)', lineHeight: '1.5' }}>
              Are you sure you want to regenerate your API key? This action is <strong>permanent</strong> and will immediately invalidate your existing key. Any servers or applications integrating with PayTrack using the old key will start failing.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-sm)' }}>
              <button className="btn btn-secondary" onClick={() => setShowConfirmModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" style={{ background: 'var(--danger)' }} onClick={handleRegenerateKey}>
                Confirm Regenerate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
