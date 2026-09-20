# Manual Test Checklist

This file tracks manual verification steps that must be completed by the developer.
Automated tests do NOT substitute for these checks.

---

## PHASE 2A — Backend Foundation + Database

### Manual Test 1 — Environment Setup

```powershell
# Step 1: Activate the virtual environment (from project root)
cd "c:\Users\priti\Downloads\multimedia project"
.\.venv\Scripts\Activate.ps1

# You should see: (.venv) in your prompt

# Step 2: Install backend dependencies
pip install -r backend\requirements.txt

# Step 3: Configure .env
copy backend\.env.example backend\.env
# Then EDIT backend\.env and set DATABASE_URL to your PostgreSQL connection string.
# Example:
#   DATABASE_URL=postgresql+psycopg2://postgres:yourpassword@localhost:5432/content_provenance

# Step 4: Start PostgreSQL
# (see docs/PHASE2A_IMPLEMENTATION.md section 7)

# Step 5: Create the database (if it doesn't exist)
# Run in psql or pgAdmin:
#   CREATE DATABASE content_provenance;

# Step 6: Verify the DATABASE_URL from Python
cd backend
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
# Expected: prints your full DATABASE_URL without error
```

**Checklist:**
- [ ] Virtual environment activated
- [ ] Dependencies installed without errors
- [ ] `.env` file created from `.env.example`
- [ ] `DATABASE_URL` printed correctly from Python

---

### Manual Test 2 — Database Migration (Alembic upgrade)

Run from the `backend/` directory with venv active:

```powershell
# Apply all migrations
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgreSQLImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001_initial_schema, Initial schema: ...
```

**Inspect tables in psql:**
```sql
\c content_provenance
\dt
```

**Expected `\dt` output:**
```
              List of relations
 Schema |         Name          | Type  |  Owner
--------+-----------------------+-------+----------
 public | alembic_version       | table | postgres
 public | provenance_records    | table | postgres
 public | verification_records  | table | postgres
 public | watermarked_assets    | table | postgres
```

**Inspect table structure:**
```sql
\d provenance_records
\d watermarked_assets
\d verification_records
```

**Checklist:**
- [ ] `alembic upgrade head` completes without error
- [ ] `\dt` shows all 3 tables + `alembic_version`
- [ ] `\d provenance_records` shows all columns including `provenance_uuid`, `metadata`, `created_at`
- [ ] `\d watermarked_assets` shows `sha256`, `watermark_delta`, `provenance_record_id` FK
- [ ] `\d verification_records` shows `verdict` column with CHECK constraint

---

### Manual Test 3 — Alembic Downgrade + Re-Upgrade

```powershell
# From backend/

# Step 1: Downgrade one revision
alembic downgrade -1
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running downgrade 0001_initial_schema -> , ...
```

**Verify in psql:**
```sql
\dt
```
**Expected:** Only `alembic_version` table remains (or no tables at all).

```powershell
# Step 2: Re-apply migrations
alembic upgrade head
```

**Expected:** Same output as Test 2. All 3 tables are recreated.

**Verify in psql again:**
```sql
\dt
```

**Checklist:**
- [ ] `alembic downgrade -1` succeeds
- [ ] After downgrade, business tables are gone
- [ ] `alembic upgrade head` succeeds again
- [ ] All 3 tables are recreated correctly

---

### Manual Test 4 — FastAPI Server + Health Endpoint

```powershell
# From backend/ with venv active:
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Expected startup log:**
```
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Check 1: Swagger UI**
Open browser: `http://127.0.0.1:8000/docs`

Expected: Swagger UI page with title "Content Provenance Watermarking API", showing the `GET /health` endpoint.

**Check 2: Health endpoint via browser or curl**
```powershell
curl http://127.0.0.1:8000/health
```

**Expected response:**
```json
{"status": "ok", "database": "ok"}
```

> If PostgreSQL is not running, `database` will show `"unreachable"` but `status` will still be `"ok"`. This is correct behaviour.

**Check 3: OpenAPI schema**
```powershell
curl http://127.0.0.1:8000/openapi.json
```

Expected: JSON document with `"title": "Content Provenance Watermarking API"` and `/health` listed under `paths`.

**Checklist:**
- [ ] `uvicorn` starts without error
- [ ] `http://127.0.0.1:8000/docs` opens Swagger UI
- [ ] `GET /health` returns `{"status": "ok", ...}`
- [ ] `database` field is `"ok"` (requires Postgres running + migrations applied)
- [ ] `/openapi.json` returns valid schema

---

### Manual Test 5 — SQLAlchemy Database Insert/Read

With PostgreSQL running and migrations applied:

```powershell
# From backend/ with venv active:
python dev_verify_db.py
```

**Expected output:**
```
[OK] Database connection established
[OK] Inserted ProvenanceRecord: id=<some-uuid>
[OK] Read back record: source_type='ai_generated'  provenance_uuid=<some-uuid>
[OK] Verification complete. Cleaning up...
[OK] Done.
```

If the database is unreachable:
```
[FAIL] Cannot connect to database. Check DATABASE_URL in .env
```

**Checklist:**
- [ ] `dev_verify_db.py` runs without error
- [ ] `[OK] Database connection established` is printed
- [ ] `[OK] Inserted ProvenanceRecord` is printed with a valid UUID
- [ ] `[OK] Read back record` matches what was inserted
- [ ] `[OK] Done.` is printed (record was cleaned up)

---

### Manual Test 6 — Automated Tests

```powershell
# From project root with venv active:
$env:PYTHONPATH="backend"
.venv\Scripts\python -m pytest backend/tests/ -v
```

**Expected:**
```
13 passed, 6 warnings in X.XXs
```

(6 warnings are cosmetic FastAPI deprecations about `on_event`. They do not affect functionality.)

**Checklist:**
- [ ] All 13 automated tests pass
- [ ] No test failures

---

### Phase 2A Sign-Off

Only mark complete once ALL checklist items above are verified:

- [ ] Manual Test 1 — Environment passed
- [ ] Manual Test 2 — Database migration passed
- [ ] Manual Test 3 — Downgrade/re-upgrade passed
- [ ] Manual Test 4 — FastAPI health endpoint passed
- [ ] Manual Test 5 — SQLAlchemy insert/read passed
- [ ] Manual Test 6 — Automated tests 13/13 passed
