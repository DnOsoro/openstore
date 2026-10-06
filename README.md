# OpenStore AI Analytics

Ask your data a question in plain English and get back the SQL, a results table, and a chart.

**Live demo:** https://openstore-delta.vercel.app

OpenStore AI Analytics is an end-to-end analytics project. It combines a data engineering pipeline (ingestion, loading, validation, transformation, analytics views) with an AI query layer that turns natural language into guarded, read-only SQL against PostgreSQL.

---

## The Problem

In many teams, a simple question like "Which state generated the most revenue?" turns into a chain of steps: a request to an analyst, a SQL query, validation, and a report, all before anyone gets an answer.

This project makes that process direct, while keeping the generated SQL safe and the underlying data trustworthy.

---

## How It Works

1. The user types a question in plain English.
2. The backend sends the question, plus the database schema, to an LLM (Gemini via OpenRouter).
3. The LLM returns a SQL query.
4. The query passes through guardrails before it touches the database.
5. The validated query runs against PostgreSQL.
6. The frontend shows the SQL, a results table, and a bar chart.

```mermaid
flowchart LR
    A[User question] --> B[Next.js frontend]
    B --> C[FastAPI backend]
    C --> D[OpenRouter / Gemini]
    D --> E[Generated SQL]
    E --> F[Guardrails]
    F --> G[(PostgreSQL)]
    G --> H[Table + chart]
```

---

## Data Pipeline

The project uses a layered architecture so the AI queries curated data instead of raw tables.

```mermaid
flowchart LR
    A[CSV files] --> B[SeaweedFS data lake]
    B --> C[raw schema]
    C --> D[Pandera validation]
    C --> E[staging schema]
    E --> F[core schema]
    F --> G[analytics views]
    G --> H[AI query layer]
```

| Layer | Schema | Purpose |
|-------|--------|---------|
| Data lake | SeaweedFS bucket | Stores the original CSV files behind an S3-compatible API |
| Raw | `raw` | Untouched copy of each CSV loaded into PostgreSQL |
| Staging | `staging` | Type casting and column renaming (timestamps, integers, numerics) |
| Core | `core` | Dimension and fact tables: `dim_customers`, `fct_orders` |
| Analytics | `analytics` | Business-ready views used by the dashboard and the AI |

### Analytics views

- `analytics.monthly_revenue_summary`: monthly orders, revenue, product sales, freight fees, and average order value for delivered orders
- `analytics.revenue_by_location`: orders and revenue by customer state and city
- `analytics.delivery_performance`: delivery time in days and on-time or delayed status per order

### Data quality

`src/quality/validate_data.py` uses Pandera to validate the raw tables before transformation. Checks include non-null keys, valid order statuses, positive prices, non-negative freight values, and valid item numbers.

---

## SQL Guardrails

Generated SQL is never executed directly. `src/api/guardrails.py` applies these checks first:

- Rejects multi-statement queries
- Allows `SELECT` queries only
- Blocks DDL and DML keywords: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `GRANT`, `REVOKE`, `EXEC`, `EXECUTE`, and `pg_*` system objects
- Appends `LIMIT 100` when the query has no limit

The frontend displays the validated SQL so users can see exactly what ran.

---

## Tech Stack

| Area | Technology |
|------|------------|
| Database | PostgreSQL 15 |
| Data lake | SeaweedFS (S3-compatible) |
| Backend | Python, FastAPI, SQLAlchemy, psycopg2 |
| Data processing | pandas, boto3 |
| Data quality | Pandera |
| LLM | Gemini via OpenRouter (default: `google/gemini-2.5-flash`) |
| Frontend | Next.js, React, TypeScript, Tailwind CSS, Recharts, lucide-react |
| Infrastructure | Docker Compose (local), Vercel (deployment) |

---

## Project Structure

```
openstore/
├── api/
│   └── index.py                  # Vercel entry point for the FastAPI app
├── frontend/                     # Next.js application
│   └── src/app/
│       ├── page.tsx              # Main UI: query box, SQL, table, charts
│       ├── layout.tsx
│       └── globals.css
├── src/
│   ├── ingestion/
│   │   └── upload_to_seaweed.py  # Upload CSVs to the SeaweedFS bucket
│   ├── loading/
│   │   └── load_to_postgres.py   # Load CSVs from SeaweedFS into the raw schema
│   ├── quality/
│   │   └── validate_data.py      # Pandera data quality checks
│   ├── transform/
│   │   ├── staging_transform.py  # raw -> staging
│   │   └── core_transform.py     # staging -> core
│   ├── analytics/
│   │   └── create_views.py       # Builds analytics views
│   └── api/
│       ├── main.py               # FastAPI app and routes
│       ├── llm_service.py        # OpenRouter / Gemini integration
│       └── guardrails.py         # SQL validation and safe execution
├── docker-compose.yml            # SeaweedFS + PostgreSQL
├── requirements.txt
├── vercel.json
└── .env.example
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/v1/ai-query` | Natural language question in, validated SQL and results out |
| GET | `/api/v1/analytics/monthly-revenue` | Monthly revenue series |
| GET | `/api/v1/analytics/delivery-performance` | Delivery performance data |
| GET | `/api/v1/analytics/location-revenue` | Revenue by state and city |

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/ai-query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Which state generated the most revenue?"}'
```

Example response shape:

```json
{
  "status": "success",
  "prompt": "Which state generated the most revenue?",
  "validated_sql": "SELECT ... LIMIT 100;",
  "rows_returned": 1,
  "data": [{ "customer_state": "...", "total_revenue": "..." }]
}
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- An [OpenRouter](https://openrouter.ai) API key
- The Olist Brazilian E-Commerce CSV files (orders, order items, and customers at minimum)

### 1. Clone and install

```bash
git clone https://github.com/dnosoro/openstore.git
cd openstore

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example file and fill it in:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | PostgreSQL credentials |
| `POSTGRES_HOST`, `POSTGRES_PORT` | PostgreSQL host and port |
| `DATABASE_URL` | Full connection string, e.g. `postgresql://user:pass@localhost:5432/dbname` |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `LLM_MODEL` | Model name (default `google/gemini-2.5-flash`) |
| `NEXT_PUBLIC_API_URL` | Backend URL used by the frontend |

Optional (defaults are used for local development): `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`.

Some scripts read `DATABASE_URL` and others read the individual `POSTGRES_*` variables, so keep both consistent.

### 3. Start the infrastructure

```bash
docker compose up -d
```

This starts SeaweedFS (S3 gateway on port 8333) and PostgreSQL (port 5432).

### 4. Run the pipeline

Place the Olist CSV files in `data/source/`, then run the steps in order:

```bash
python -m src.ingestion.upload_to_seaweed    # CSVs -> SeaweedFS
python -m src.loading.load_to_postgres       # SeaweedFS -> raw schema
python -m src.quality.validate_data          # Pandera checks
python -m src.transform.staging_transform    # raw -> staging
python -m src.transform.core_transform       # staging -> core
python -m src.analytics.create_views         # analytics views
```

### 5. Start the API

```bash
uvicorn src.api.main:app --reload --port 8000
```

API docs are available at `http://localhost:8000/docs`.

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`, then open `http://localhost:3000`.

---

## Example Questions

- Which state generated the most revenue?
- Show the top 5 cities by total revenue
- What is the average order value by month?
- How many orders were delivered late?
- What is the average delivery time in days?

---

## Deployment

The app is deployed on Vercel. `vercel.json` routes requests to `api/index.py`, which exposes the FastAPI app. Set `DATABASE_URL`, `OPENROUTER_API_KEY`, `LLM_MODEL`, and `NEXT_PUBLIC_API_URL` as environment variables in the Vercel project settings, and point `DATABASE_URL` at a PostgreSQL instance reachable from the deployment.

---

## Lessons Learned

The hardest part of this project was not getting the AI to generate SQL. It was everything around it:

- Database connections that worked locally but failed in deployment
- API responses that did not match expectations
- Environment variable handling across local, Docker, and hosted environments
- Controlling generated SQL before it reaches the database

The main takeaway: AI does not remove the need for good data engineering, it makes it more important. A language model can write a query in seconds, but if the data is unreliable or the query is unsafe, you just get a faster way to produce the wrong answer.

---

## Known Limitations and Next Steps

- Guardrails are pattern-based. A stronger setup would also connect with a read-only PostgreSQL role and enforce a statement timeout.
- CORS is currently open (`*`) for demo purposes and should be restricted to known origins in production.
- Staging tables use `CREATE TABLE IF NOT EXISTS`, so re-running the transform will not refresh existing tables. Switching to drop-and-recreate or incremental loads would fix this.
- The frontend always renders a bar chart using the first two columns of the result. Chart type selection based on result shape would improve this.
- The LLM prompt covers a fixed set of tables. Loading the schema dynamically would make it easier to extend.
- No automated tests yet.

---

## Dataset

This project uses the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

---

## Author

Built by Chanai Dnosoro. Feedback and suggestions are welcome.
