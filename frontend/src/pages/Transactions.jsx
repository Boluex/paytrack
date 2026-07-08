import { useState, useEffect } from 'react';
import client from '../api/client';
import Navbar from '../components/Navbar';
import TransactionTable from '../components/TransactionTable';

const STATUSES = ['all', 'completed', 'pending', 'failed', 'flagged'];

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTransactions();
  }, [page, statusFilter]);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 20 };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (search) params.search = search;
      const res = await client.get('/transactions', { params });
      setTransactions(res.data.transactions);
      setTotalPages(res.data.total_pages);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Failed to fetch transactions', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchTransactions();
  };

  return (
    <div className="app-layout">
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <h1>Transactions</h1>
          <p>{total} total transactions</p>
        </div>

        <div className="table-container">
          <div className="table-header">
            <div className="table-filters">
              {STATUSES.map((s) => (
                <button
                  key={s}
                  className={`filter-btn ${statusFilter === s ? 'active' : ''}`}
                  onClick={() => { setStatusFilter(s); setPage(1); }}
                >
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>

            <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                className="form-input"
                type="text"
                placeholder="Search by customer email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ width: '240px', padding: '0.5rem 0.75rem', fontSize: '0.85rem' }}
              />
              <button className="btn btn-secondary" type="submit" style={{ padding: '0.5rem 1rem' }}>
                Search
              </button>
            </form>
          </div>

          {loading ? (
            <div className="loading-container"><div className="spinner" /></div>
          ) : (
            <TransactionTable transactions={transactions} />
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                ← Prev
              </button>
              <span className="page-info">Page {page} of {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                Next →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
