# DB Assessment — Multi-Database Data Integration Platform

A full-stack application for connecting to heterogeneous databases, extracting data in batches, editing it in an interactive grid, and storing results with dual persistence (database + file export) under role-based access control.

## Architecture

```
External Databases (Postgres | MySQL | MongoDB | ClickHouse)
        │
        ▼
  Connector Layer (Strategy Pattern)
        │
  Batch Extraction Engine
        │
        ▼
  Frontend Editable Grid (Next.js)
        │
  User Modifies Data
        │
        ▼
  Backend Processing (Django REST Framework)
        │
  ┌─────────────┬──────────────┐
  ▼             ▼              ▼
Store in DB   Export JSON   Export CSV
  (Postgres)
        │
  RBAC Access Control Layer
```

## Project Structure

```
db-assessment/
├── docker/                  # DB init scripts
│   ├── postgres/init.sql
│   ├── mysql/init.sql
│   ├── mongo/init.js
│   └── clickhouse/init.sql
├── backend/                 # Django REST Framework
│   ├── apps/
│   │   ├── accounts/        # User model, JWT auth, RBAC
│   │   ├── connections/     # ConnectionConfig + Connector abstraction
│   │   ├── extraction/      # Batch extraction engine
│   │   └── storage/         # Dual storage + file management
│   └── config/              # Django settings & URLs
├── frontend/                # Next.js + Tailwind CSS
│   └── src/
│       ├── components/      # EditableGrid, ConnectionForm, Layout
│       ├── context/         # AuthContext (JWT)
│       ├── pages/           # login, register, dashboard, connections, extract, files
│       └── services/        # API client with interceptors
└── docker-compose.yml
```

## Quick Start

```bash
docker-compose up --build
```

This starts:
| Service        | Port   |
|----------------|--------|
| Frontend       | 3000   |
| Backend API    | 8000   |
| Main DB        | 5434   |
| PostgreSQL (test) | 5433 |
| MySQL (test)   | 3307   |
| MongoDB (test) | 27018  |
| ClickHouse (test)| 8124 |

## Usage

1. Register at `http://localhost:3000/register`
2. Create a database connection (Connections page)
3. Select connection → table → batch size → Extract
4. Edit data in the interactive grid (double-click cells)
5. Choose export format (JSON/CSV) → Submit
6. View/download/share files on the Files page

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register user |
| POST | `/api/auth/login/` | Get JWT tokens |
| GET | `/api/auth/profile/` | Current user profile |
| GET/POST | `/api/connections/` | List/create connections |
| POST | `/api/connections/{id}/test/` | Test connection |
| GET | `/api/connections/{id}/tables/` | List tables |
| POST | `/api/extraction/extract/` | Extract data batch |
| POST | `/api/storage/submit/` | Submit & export data |
| GET | `/api/storage/files/` | List exported files |
| GET | `/api/storage/files/{id}/download/` | Download file |
| POST | `/api/storage/files/{id}/share/` | Toggle file sharing |

## RBAC

| Role | Access |
|------|--------|
| Admin | All connections, records, files |
| User | Own connections, records, own + shared files |
