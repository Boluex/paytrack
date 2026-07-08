export default function TransactionTable({ transactions, compact = false }) {
  if (!transactions || transactions.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No transactions yet
      </div>
    );
  }

  const formatAmount = (amount, currency) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency: currency || 'USD',
    }).format(amount);
  };

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  };

  return (
    <table>
      <thead>
        <tr>
          <th>Transaction ID</th>
          <th>Amount</th>
          <th>Status</th>
          {!compact && <th>Customer</th>}
          {!compact && <th>Fraud Score</th>}
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {transactions.map((txn) => (
          <tr key={txn.id}>
            <td style={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>
              {txn.id.slice(0, 8)}...
            </td>
            <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              {formatAmount(txn.amount, txn.currency)}
            </td>
            <td>
              <span className={`badge badge-${txn.status}`}>{txn.status}</span>
            </td>
            {!compact && <td>{txn.customer_email || '—'}</td>}
            {!compact && (
              <td>
                <span style={{
                  color: txn.fraud_score >= 70 ? 'var(--danger)' :
                         txn.fraud_score >= 40 ? 'var(--warning)' : 'var(--success)',
                  fontWeight: 600,
                }}>
                  {txn.fraud_score}
                </span>
              </td>
            )}
            <td>{formatDate(txn.created_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
