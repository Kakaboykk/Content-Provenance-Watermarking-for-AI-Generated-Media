# Content-Provenance Watermarking Backend

FastAPI backend service powering frequency-domain watermarking, PostgreSQL provenance tracking, and AI image detection.

---

## Tech Stack

- **Framework**: [FastAPI 0.115](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **Database ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Database Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Database Driver**: [psycopg2-binary](https://www.psycopg.org/)
- **Validation & Settings**: [Pydantic v2](https://docs.pydantic.dev/) + `pydantic-settings`
- **Testing**: [pytest](https://docs.pytest.org/) + `pytest-asyncio` + `httpx`

---

## Architecture & Endpoints

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/health` | `GET` | Health check & DB connection verification |
| `/generate` | `POST` | Generates AI image via Hugging Face, Stability AI, or mock generator |
| `/watermark/embed` | `POST` | Embeds 192-bit DWT-DCT payload & registers asset in PostgreSQL |
| `/verify` | `POST` | Extracts blind watermark, checks ledger, runs crop diagnostic & AI detector |
| `/detect-ai` | `POST` | Evaluates probabilistic AI-vs-human score via Sightengine or HF classifier |

---

## Quickstart

### 1. Python Environment

```bash
# From the backend directory
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
pip install -e ..
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your credentials:
```bash
cp .env.example .env
```

### 3. Migrations

Apply Alembic migrations to your PostgreSQL database:
```bash
alembic upgrade head
```

### 4. Run Server

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive OpenAPI Swagger documentation will be available at:
`http://localhost:8000/docs`
