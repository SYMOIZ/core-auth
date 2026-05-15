# Core-Auth API

> A plug-and-play async authentication engine — register, login, refresh tokens, logout, and block stolen tokens. Built with FastAPI + SQLAlchemy + Redis + JWT.

---

## What Problem Does This Solve?

Almost every app needs users to sign up, log in, and stay logged in securely. Building auth from scratch is repetitive and easy to get wrong. Core-Auth gives you a complete, production-ready auth backend you can run in two commands and connect any frontend or mobile app to.

**Who is this for?**
- Developers building a SaaS product who need auth out of the box
- Students learning how real-world JWT auth works end to end
- Backend engineers who want a reference implementation for async Python auth

---

## What It Does (Plain English)

| Action | What Happens |
|---|---|
| User signs up | Email + password saved. Password is **never stored plain** — it's hashed with bcrypt before touching the database |
| User logs in | Server checks password hash → hands back two tokens: a short-lived **access token** (15 min) and a long-lived **refresh token** (7 days) |
| User visits a protected page | Client sends the access token → server verifies it → returns the data |
| Access token expires | Client sends the refresh token → server issues a brand new pair |
| User logs out | Access token is written to Redis with a countdown timer — when the timer hits zero, the entry deletes itself. Token is **dead immediately**, not just "forgotten" |
| Stolen token is replayed | Server checks Redis → token is blacklisted → **401 Unauthorized** — zero-trust enforced |

---

## Tech Stack

| What | Tool | Why |
|---|---|---|
| Web framework | FastAPI | Async, fast, auto-generates API docs |
| Database ORM | SQLAlchemy 2.0 (async) | Type-safe DB queries, works with SQLite and Postgres |
| Dev database | SQLite + aiosqlite | Zero setup — just run the server |
| Prod database | PostgreSQL + asyncpg | High-performance async Postgres driver |
| Migrations | Alembic | Version-controlled schema changes |
| Token blacklist | Redis (async) | Sub-millisecond token lookups, auto-expiring keys |
| Auth tokens | python-jose (JWT, HS256) | Industry-standard signed tokens |
| Password hashing | passlib + bcrypt | Slow-by-design hashing — brute force resistant |
| Config | pydantic-settings | Type-safe `.env` loading, crashes fast if a secret is missing |
| Package manager | UV | Replaces pip + venv, 10-100x faster |
| HTTP test client | HTTPX (async) | Tests hit the real ASGI app in-process |
| Test runner | pytest + pytest-asyncio | Async test support |
| Linter | flake8 | Style enforcement |
| Security scanner | bandit | Catches common Python security bugs |

---

## Project Structure

```
Auth Project/
│
├── .env                          # Your secrets (never committed to git)
├── pyproject.toml                # All dependencies + pytest settings
├── alembic.ini                   # Database migration config
├── coreauth.db                   # SQLite database (auto-created, dev only)
│
├── app/                          # All application code lives here
│   ├── main.py                   # Entry point — wires everything together
│   │
│   ├── core/
│   │   ├── config.py             # Reads .env → typed Settings object
│   │   └── security.py           # Hashing, JWT create/decode
│   │
│   ├── db/
│   │   ├── session.py            # Database connection + session per request
│   │   └── redis.py              # Redis connection + blacklist helpers
│   │
│   ├── models/
│   │   └── user.py               # The `users` table schema
│   │
│   ├── schemas/
│   │   ├── user.py               # What the API accepts/returns for users
│   │   └── token.py              # What the API returns for tokens
│   │
│   ├── services/
│   │   └── auth_service.py       # Business logic (no HTTP concerns here)
│   │
│   └── api/routes/
│       ├── auth.py               # /auth/register, login, refresh, logout
│       └── users.py              # /users/me + auth guard dependency
│
├── tests/
│   ├── conftest.py               # Test database, Redis, HTTP client setup
│   └── test_auth.py              # 6 end-to-end tests
│
├── alembic/
│   ├── env.py                    # Async migration runner
│   └── versions/                 # Generated migration files go here
│
└── reports/
    └── test_report.html          # HTML test report (generated on demand)
```

---

## Step-by-Step Setup

### Step 1 — Prerequisites

Make sure you have these installed:

- **Python 3.13+** — check with `python --version`
- **UV** — install with `pip install uv` or follow [docs.astral.sh/uv](https://docs.astral.sh/uv)
- **Redis** — needed for logout/blacklisting. Install options:
  - Windows: [Redis for Windows](https://github.com/microsoftarchive/redis/releases) or via WSL
  - Mac: `brew install redis && brew services start redis`
  - Linux: `sudo apt install redis-server && sudo systemctl start redis`

---

### Step 2 — Clone and Enter the Project

```bash
git clone https://github.com/SYMOIZ/core-auth.git
cd core-auth
```

---

### Step 3 — Create Your `.env` File

Create a file called `.env` in the project root with this content:

```env
DATABASE_URL=sqlite+aiosqlite:///./coreauth.db
REDIS_URL=redis://localhost:6379
ACCESS_TOKEN_SECRET=change-this-to-a-long-random-string
REFRESH_TOKEN_SECRET=change-this-to-a-different-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

> Generate strong secrets with: `python -c "import secrets; print(secrets.token_hex(32))"`

---

### Step 4 — Install Dependencies

```bash
uv sync
```

This reads `pyproject.toml` and installs every dependency into an isolated `.venv`. Takes about 30 seconds the first time.

---

### Step 5 — Start the Server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
[OK] Database tables ready
[OK] Redis connection established
```

The SQLite database and `users` table are created automatically. You do not need to run any migration commands for local development.

---

### Step 6 — Open the API Docs

Go to **http://localhost:8000/docs** in your browser.

You will see the Swagger UI — an interactive page where you can try every endpoint without writing any code. Click an endpoint, hit **Try it out**, fill in the fields, and click **Execute**.

---

## Using the API — Step by Step

### 1. Register a new user

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "YourPassword123"}'
```

**Response:**
```json
{
  "id": 1,
  "email": "you@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-05-15T12:00:00"
}
```

Notice: no password or hash in the response — ever.

---

### 2. Log in

```bash
curl -X POST http://localhost:8000/auth/login \
  -F "username=you@example.com" \
  -F "password=YourPassword123"
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

Save both tokens. The access token is valid for 15 minutes.

---

### 3. Access a protected route

```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer eyJhbGci..."
```

**Response:**
```json
{
  "id": 1,
  "email": "you@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-05-15T12:00:00"
}
```

---

### 4. Refresh your tokens (when access token expires)

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGci..."}'
```

**Response:** A brand new `access_token` + `refresh_token` pair.

---

### 5. Log out

```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGci..."}'
```

**Response:**
```json
{ "detail": "Successfully logged out" }
```

The access token is now blacklisted in Redis. Any further requests with it return **401**.

---

### 6. Try the blacklisted token (zero-trust proof)

```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer eyJhbGci..."
```

**Response:**
```json
{ "detail": "Token has been revoked" }
```

Status code: **401 Unauthorized** — even though the token's signature is valid and it hasn't expired. This is what zero-trust means.

---

## All API Endpoints

| Method | Endpoint | Auth required | Description |
|---|---|---|---|
| GET | `/` | No | Health check |
| POST | `/auth/register` | No | Create a new account |
| POST | `/auth/login` | No | Login, receive token pair |
| POST | `/auth/refresh` | No (refresh token) | Issue new token pair |
| POST | `/auth/logout` | No (access token) | Blacklist access token |
| GET | `/users/me` | Yes (Bearer) | Get logged-in user profile |
| GET | `/docs` | No | Swagger UI |
| GET | `/redoc` | No | ReDoc UI |

---

## Running the Tests

```bash
uv run pytest tests/ -v --asyncio-mode=auto
```

Expected output:

```
PASSED  test_register_user
PASSED  test_login_user
PASSED  test_access_protected_route
PASSED  test_refresh_token
PASSED  test_logout
PASSED  test_blacklisted_token

6 passed in 2.10s
```

### What each test proves

| Test | What it verifies |
|---|---|
| `test_register_user` | Account is created, password is never returned |
| `test_login_user` | Valid credentials return a token pair |
| `test_access_protected_route` | Bearer token lets you through the auth guard |
| `test_refresh_token` | Refresh token produces a new valid pair |
| `test_logout` | Logout succeeds and returns a confirmation message |
| `test_blacklisted_token` | Logged-out token is rejected with 401 |

### Generate an HTML report

```bash
uv run pytest tests/ -v --asyncio-mode=auto \
  --html=reports/test_report.html \
  --self-contained-html
```

Open `reports/test_report.html` in your browser for a formatted visual report.

---

## Linting and Security Checks

```bash
# Check code style (must return 0 issues)
uv run flake8 app/ tests/ --max-line-length=88 --extend-ignore=E501

# Scan for security issues (must return no medium/high findings)
uv run bandit -r app/ -ll --format txt
```

---

## Switching to PostgreSQL for Production

**Step 1** — Update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/coreauth
```

**Step 2** — Create your Postgres database, then run migrations:

```bash
uv run alembic revision --autogenerate -m "initial"
uv run alembic upgrade head
```

That's it. No other code changes needed — SQLAlchemy handles the rest.

---

## How Each Piece of Code Works

### `app/core/config.py` — Settings loader
Reads `.env` into a typed Python object. If `ACCESS_TOKEN_SECRET` is missing, the app refuses to start. No silent failures.

### `app/core/security.py` — Crypto functions
- Hashes passwords with bcrypt (slow by design — makes brute force impractical)
- Creates signed JWTs with an expiry and a `type` claim (`access` or `refresh`)
- Decodes tokens — rejects expired, tampered, or wrong-type tokens with HTTP 401

### `app/db/session.py` — Database connection
Creates one async engine shared across the app. Each HTTP request gets its own database session that auto-commits on success and auto-rolls-back on error.

### `app/db/redis.py` — Token blacklist
Holds one async Redis client. `blacklist_token` writes `SETEX blacklist:<token> <ttl> 1` — Redis deletes the key automatically when the token would have expired anyway, so the blacklist never accumulates garbage.

### `app/models/user.py` — Database table

| Column | Type | Details |
|---|---|---|
| `id` | INTEGER | Auto-incrementing primary key |
| `email` | VARCHAR | Unique, indexed for fast lookups |
| `hashed_password` | VARCHAR | bcrypt hash — the raw password is never stored |
| `is_active` | BOOLEAN | `False` = account suspended, login blocked |
| `is_superuser` | BOOLEAN | Reserved for admin elevation |
| `created_at` | DATETIME | UTC, set automatically on insert |

### `app/schemas/` — Request and response shapes
Pydantic models that validate incoming JSON and filter outgoing JSON. The `UserRegistrationResponse` schema deliberately excludes `hashed_password` — even if someone added a bug that loaded it, Pydantic would strip it before it leaves the server.

### `app/services/auth_service.py` — Business logic
No HTTP knowledge here — just pure functions that talk to the database. This separation makes logic easy to test and reuse.

### `app/api/routes/auth.py` — Auth endpoints
Thin HTTP layer that calls services and returns schemas. No business logic lives here.

### `app/api/routes/users.py` — Protected endpoints + auth guard
`get_current_user` is a FastAPI dependency injected into any route that needs auth. It: extracts the Bearer token → checks the Redis blacklist → decodes the JWT → loads the user from DB → rejects the request at any failing step.

### `app/main.py` — App entry point
Runs startup hooks (create DB tables, connect Redis) and shutdown hooks (disconnect Redis, close DB pool). Mounts all routers.

---

## Common Questions

**Do I need Docker?**
No. For local dev, SQLite and a native Redis install are all you need.

**Can I use this with React / Vue / mobile?**
Yes. The API speaks JSON. Send the `Authorization: Bearer <token>` header from any client.

**How do I make a route require login?**
Add `current_user: User = Depends(get_current_user)` to any route function. FastAPI handles the rest.

**What happens if Redis is down?**
Logout and the blacklist check will fail. Login and registration still work. For high availability, point `REDIS_URL` at a Redis Sentinel or Cluster URL.

**How do I add more routes?**
Create a new file in `app/api/routes/`, define an `APIRouter`, and mount it in `app/main.py` with `app.include_router(...)`.

---

## License

MIT — use it, modify it, ship it.
