# DB Assessment — Multi-Database Data Integration Platform

A full-stack application for connecting to heterogeneous databases (PostgreSQL, MySQL, MongoDB, ClickHouse), extracting data in batches, editing it in an interactive grid, and storing results with dual persistence (database + file export) under role-based access control.

**Tech Stack:** Django REST Framework · Next.js · Tailwind CSS · Docker · PostgreSQL · JWT Auth

---

## Quick Start (1 command)

```bash
make up
```

Or without Make:

```bash
docker-compose up --build -d
```

Then open **http://localhost:3000** and log in:

| Account | Username | Password |
|---------|----------|----------|
| Admin | `admin` | `admin123` |
| User | `demo` | `demo1234` |

> All 4 demo database connections are pre-configured. Go to **Connections** → **Test** any connection, then **Extract Data** to see it working.

---

## What It Does

```
External Databases (Postgres · MySQL · MongoDB · ClickHouse)
        │
        ▼
  Connector Abstraction Layer (Strategy Pattern)
        │
  Batch Extraction Engine
        │
        ▼
  Editable Data Grid (Next.js)
        │
  User Edits Data
        │
        ▼
  Dual Storage
  ├── Database (structured records)
  └── File Export (JSON / CSV with metadata)
        │
  RBAC Access Control
```

### Key Features

- **Multi-DB Connectivity** — Plug-and-play connectors via Strategy Pattern
- **Batch Extraction** — Paginated data pulls with configurable batch sizes
- **Interactive Grid** — Double-click any cell to edit, Submit to save
- **Dual Storage** — Every submission saves to DB + generates a timestamped file
- **RBAC** — Admin sees everything; Users see own data + shared files
- **Dockerized** — Full stack runs with one command, including 4 test databases with seed data

---

## Architecture

### Backend (`backend/`)

```
apps/
├── accounts/        # Custom User model, JWT auth, RBAC permissions
├── connections/     # ConnectionConfig model + Connector abstraction
│   └── connectors/  # BaseConnector → Postgres, MySQL, Mongo, ClickHouse
├── extraction/      # Batch extraction engine with validation
└── storage/         # Dual storage (DB + file) with RBAC file sharing
```

**Design Decisions:**
- **Connector Strategy Pattern** — Each DB type implements `BaseConnector` (connect, fetch_batch, list_tables, close). New DB types are added by implementing one class and registering in the factory. No `if/elif` chains.
- **SQL Injection Prevention** — Table names validated via regex whitelist before any query execution
- **Path Traversal Prevention** — File downloads verified against exports directory
- **RBAC at API level** — Permissions enforced on every endpoint via DRF permission classes, not just frontend

### Frontend (`frontend/`)

```
src/
├── components/      # EditableGrid, ConnectionForm, Layout, Spinner, EmptyState
├── context/         # AuthContext (JWT token management)
├── hooks/           # useRequireAuth (centralized auth guard)
├── pages/           # login, register, dashboard, connections, extract, files
└── services/        # Axios client with JWT interceptors + auto-refresh
```

### Infrastructure (`docker/`)

| Service | Container | Port |
|---------|-----------|------|
| Frontend (Next.js) | `frontend` | 3000 |
| Backend (Gunicorn) | `backend` | 8000 |
| Main DB (PostgreSQL) | `main_db` | 5434 |
| Test PostgreSQL | `postgres_test` | 5433 |
| Test MySQL | `mysql_test` | 3307 |
| Test MongoDB | `mongo_test` | 27018 |
| Test ClickHouse | `clickhouse_test` | 8124 |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register user |
| POST | `/api/auth/login/` | Get JWT tokens |
| GET | `/api/auth/profile/` | Current user profile |
| GET/POST | `/api/connections/` | List/create connections |
| POST | `/api/connections/{id}/test/` | Test connection |
| GET | `/api/connections/{id}/tables/` | List tables for connection |
| GET | `/api/connections/{id}/tables/{name}/columns/` | List columns |
| POST | `/api/extraction/extract/` | Extract data batch |
| GET | `/api/extraction/jobs/` | Extraction history |
| POST | `/api/storage/submit/` | Submit edited data + export file |
| GET | `/api/storage/records/` | List processed records |
| GET | `/api/storage/files/` | List exported files |
| GET | `/api/storage/files/{id}/download/` | Download file |
| POST | `/api/storage/files/{id}/share/` | Toggle file sharing |

---

## Testing

```bash
make test
```

**22 tests** covering:
- Authentication (register, login, token, profile)
- SQL injection prevention (9 attack vectors rejected)
- RBAC enforcement (user isolation, admin access, cross-user denial)
- Extraction permissions (owner/non-owner access)
- Data submission permissions

---

## Development

```bash
# Hot-reload mode (watches file changes)
make dev

# View logs
make logs

# Stop everything
make down

# Full cleanup (removes volumes)
make clean
```

---

## RBAC Model

| Role | Connections | Extraction | Records | Files |
|------|-------------|------------|---------|-------|
| Admin | All | All | All | All |
| User | Own | Own connections | Own | Own + Shared |
