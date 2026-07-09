#  PayTrack — Payment Transaction Monitor

A full-stack payment monitoring platform where merchants register, log transactions via API, view real-time dashboards, receive webhook notifications, and get alerted to suspicious activity through automated fraud detection.


##  Start

### Prerequisites
- Docker & Docker Compose
- OR: Python 3.13+, Node.js 20+, PostgreSQL 15+, Redis 7+

### Option 1: Docker Compose (Recommended)

```bash
git clone <repo-url>
cd PayTrack
docker compose up --build
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Option 2: Local Development

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Make sure PostgreSQL and Redis are running locally
cp .env.example .env  # edit with your DB/Redis URLs

uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

##  API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register a merchant |
| `POST` | `/api/auth/login` | Login and get JWT |
| `GET` | `/api/auth/me` | Get current merchant profile + API key |

### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/transactions` | Log a new transaction |
| `GET` | `/api/transactions` | List transactions (paginated, filterable) |
| `GET` | `/api/transactions/stats` | Dashboard statistics |
| `GET` | `/api/transactions/{id}` | Get single transaction |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/webhooks` | Get webhook config |
| `PUT` | `/api/webhooks` | Set/update webhook URL |
| `DELETE` | `/api/webhooks` | Remove webhook URL |

### Example: Register + Create Transaction

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "merchant@test.com", "password": "password123", "business_name": "Test Shop"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "merchant@test.com", "password": "password123"}' | jq -r '.access_token')

# Create a transaction
curl -X POST http://localhost:8000/api/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 49.99, "currency": "USD", "status": "completed", "customer_email": "buyer@example.com", "description": "Widget purchase"}'

# Get dashboard stats
curl http://localhost:8000/api/transactions/stats \
  -H "Authorization: Bearer $TOKEN"
```

##  Fraud Detection

Transactions are automatically scored against three rules:

| Rule | Points | Trigger |
|------|--------|---------|
| **Velocity** | +40 | >10 transactions from same merchant in 1 minute |
| **Amount Anomaly** | +35 | Transaction > 3x merchant's historical average |
| **Duplicate** | +30 | Same amount + customer email within 2 minutes |

- **Score ≥ 70**: Transaction is auto-flagged (status = `flagged`)
- **Score < 70**: Transaction proceeds normally

Fraud reasons are stored on each transaction for audit.

##  Webhooks

When a merchant sets a webhook URL, PayTrack sends an HTTP POST for each new transaction:

```json
{
  "event": "transaction.created",
  "transaction_id": "uuid-here",
  "amount": 49.99,
  "currency": "USD",
  "status": "completed",
  "fraud_score": 0
}
```

- **Delivery**: Via Redis queue with background worker
- **Retries**: 3 attempts with exponential backoff
- **Timeout**: 10 seconds per attempt

##  Rate Limiting

- **100 requests per minute** per IP address
- Implemented via Redis sliding window middleware
- Returns `429 Too Many Requests` when exceeded
- Health check (`/api/health`) is excluded

##  Project Structure

```
PayTrack/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, middleware
│   │   ├── config.py               # Pydantic settings (env vars)
│   │   ├── database.py             # Async SQLAlchemy engine + session
│   │   ├── models/
│   │   │   ├── merchant.py         # Merchant model (email, api_key, webhook_url)
│   │   │   └── transaction.py      # Transaction model (amount, status, fraud_score)
│   │   ├── schemas/
│   │   │   ├── auth.py             # Register, Login, Token, MerchantResponse
│   │   │   └── transaction.py      # TransactionCreate, Response, Stats
│   │   ├── routers/
│   │   │   ├── auth.py             # POST register/login, GET me
│   │   │   ├── transactions.py     # CRUD + stats
│   │   │   └── webhooks.py         # GET/PUT/DELETE webhook config
│   │   ├── services/
│   │   │   ├── auth.py             # JWT + bcrypt + get_current_merchant
│   │   │   ├── fraud.py            # 3-rule fraud scoring engine
│   │   │   └── webhook.py          # Redis queue + HTTP delivery
│   │   └── middleware/
│   │       └── rate_limit.py       # Redis sliding window rate limiter
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Router setup
│   │   ├── main.jsx                # Entry point
│   │   ├── index.css               # Premium dark theme design system
│   │   ├── api/client.js           # Axios + JWT interceptors
│   │   ├── context/AuthContext.jsx  # Auth state provider
│   │   ├── components/
│   │   │   ├── Navbar.jsx          # Top nav with active states
│   │   │   ├── ProtectedRoute.jsx  # Auth guard
│   │   │   ├── StatsCard.jsx       # Dashboard stat card
│   │   │   └── TransactionTable.jsx # Sortable transaction table
│   │   └── pages/
│   │       ├── Login.jsx           # Glassmorphism login form
│   │       ├── Register.jsx        # Register + API key reveal
│   │       ├── Dashboard.jsx       # Stats + charts + recent txns
│   │       └── Transactions.jsx    # Filterable paginated list
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

##  Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://paytrack:paytrack@localhost:5432/paytrack` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `SECRET_KEY` | `change-this-...` | JWT signing key |
| `DEBUG` | `false` | Enable debug logging |
| `RATE_LIMIT_REQUESTS` | `100` | Max requests per window |
| `RATE_LIMIT_WINDOW` | `60` | Window size in seconds |
| `FRAUD_VELOCITY_LIMIT` | `10` | Max txns/minute before flag |
| `FRAUD_AMOUNT_MULTIPLIER` | `3.0` | Flag if > Nx average |
| `FRAUD_SCORE_THRESHOLD` | `70` | Auto-flag score threshold |



##  Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `pytest` (backend) / `npm test` (frontend)
5. Submit a PR

##  License

MIT
