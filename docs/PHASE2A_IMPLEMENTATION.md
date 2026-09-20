# Phase 2A Implementation: Backend Foundation + Database

## 1. Architecture

```
Content Provenance Watermarking System
│
├── watermark/          ← FROZEN. Phase 0 engine (unchanged)
│
└── backend/            ← Phase 2A (this document)
    ├── app/
    │   ├── core/       ← Settings, DB engine, session factory
    │   ├── models/     ← SQLAlchemy ORM models
    │   ├── schemas/    ← Pydantic v2 schemas (validation + serialisation)
    │   └── api/
    │       └── routes/ ← FastAPI routers (health only in 2A)
    ├── alembic/        ← Migration scripts
    ├── tests/          ← Automated tests (SQLite in-memory, no Postgres needed)
    └── dev_verify_db.py ← Manual DB verification script
```

The `watermark/` package is intentionally left untouched. Integration with the
watermark engine will happen in a later phase.

---

## 2. Project Structure

```
backend/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── provenance.py
│   │   ├── asset.py
│   │   └── verification.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── provenance.py
│   │   ├── asset.py
│   │   └── verification.py
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           └── health.py
├── dev_verify_db.py
├── requirements.txt
├── .env.example
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_config.py
    ├── test_models.py
    └── test_health.py
```

---

## 3. Database Schema

### provenance_records
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | UUID | NOT NULL | Primary key, auto-generated |
| provenance_uuid | UUID | NOT NULL | Unique; embedded in watermark |
| source_type | VARCHAR(64) | NOT NULL | e.g. `ai_generated` |
| generation_provider | VARCHAR(128) | NULL | e.g. `openai` |
| model_name | VARCHAR(256) | NULL | e.g. `dall-e-3` |
| prompt | TEXT | NULL | Generation prompt |
| metadata | JSONB | NULL | Arbitrary JSON metadata |
| created_at | TIMESTAMPTZ | NOT NULL | Auto-set to `now()` |

### watermarked_assets
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | UUID | NOT NULL | Primary key |
| provenance_record_id | UUID | NOT NULL | FK → provenance_records.id |
| sha256 | VARCHAR(64) | NOT NULL | SHA-256 hex digest of the PNG |
| original_filename | VARCHAR(512) | NULL | Client-supplied filename |
| mime_type | VARCHAR(64) | NOT NULL | Default `image/png` |
| width | INTEGER | NOT NULL | Pixels |
| height | INTEGER | NOT NULL | Pixels |
| watermark_delta | FLOAT | NOT NULL | QIM Δ used during embedding |
| created_at | TIMESTAMPTZ | NOT NULL | Auto-set |

### verification_records
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | UUID | NOT NULL | Primary key |
| submitted_sha256 | VARCHAR(64) | NOT NULL | SHA-256 of submitted image |
| extracted_provenance_uuid | UUID | NULL | NULL when extraction fails |
| verdict | VARCHAR(32) | NOT NULL | One of four frozen values |
| details | JSONB | NULL | BER, ECC result, etc. |
| created_at | TIMESTAMPTZ | NOT NULL | Auto-set |

**verdict CHECK constraint** (enforced at DB level):
```
AUTHENTIC_UNMODIFIED | TRACED_BUT_MODIFIED | WATERMARK_UNRECOVERABLE | NO_WATERMARK_FOUND
```

---

## 4. Relationships

```
provenance_records (1)
        │
        └──────< watermarked_assets (many)   [FK: provenance_record_id → provenance_records.id CASCADE DELETE]

verification_records               [standalone — not FK-linked to the above]
```

---

## 5. Environment Variables

| Variable | Required | Example | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | `postgresql+psycopg2://postgres:changeme@localhost:5432/content_provenance` | Full SQLAlchemy connection string |
| `APP_ENV` | No | `development` | Application environment |
| `LOG_LEVEL` | No | `INFO` | Python logging level |

Copy `.env.example` to `.env` and fill in your PostgreSQL credentials.
**Never commit `.env` to version control.**

---

## 6. Alembic Usage

All commands are run from the `backend/` directory with the venv active.

```powershell
# Apply all migrations
alembic upgrade head

# Roll back one revision
alembic downgrade -1

# Roll back everything
alembic downgrade base

# Show current revision
alembic current

# Show migration history
alembic history
```

---

## 7. How to Start PostgreSQL

### Option A — PostgreSQL installed locally (Windows)
```powershell
# Start the service (run as Administrator)
net start postgresql-x64-16        # adjust version number
```

### Option B — pgAdmin
Open pgAdmin → right-click server → Connect.

### Option C — Docker (for later phases)
```powershell
docker run -d --name pg-provenance `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=changeme `
  -e POSTGRES_DB=content_provenance `
  -p 5432:5432 `
  postgres:16-alpine
```

Create the database if using a local install:
```sql
-- In psql or pgAdmin:
CREATE DATABASE content_provenance;
```

---

## 8. How to Start FastAPI

Run from the `backend/` directory:

```powershell
# Activate venv (from project root)
.\.venv\Scripts\Activate.ps1

# Start with auto-reload (development)
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server logs will show:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 9. Manual Verification Procedures

See **MANUAL_TEST_CHECKLIST.md** for step-by-step instructions.

---

## 10. Known Limitations

- **No authentication** — Phase 2A is not secured. Do not expose port 8000 publicly.
- **`/health` database field** — Will show `"unreachable"` until PostgreSQL is running and migrations are applied. This is expected in development.
- **SQLite for tests** — Automated tests use SQLite in-memory. The JSONB column type renders as `JSON` in tests. On PostgreSQL the column is JSONB (migration script uses `postgresql.JSONB` explicitly).
- **`on_event` deprecation warnings** — FastAPI shows deprecation warnings for `on_event`. These are cosmetic. Will be replaced with `lifespan` context manager in a future phase.
- **Image binary storage** — Images are NOT stored in PostgreSQL. Only metadata and SHA-256 are stored. File storage will be addressed in a later phase.
