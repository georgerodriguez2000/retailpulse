# RetailPulse

RetailPulse is an end-to-end Data Engineering portfolio project that ingests product data from a public REST API, preserves raw source snapshots, validates data quality, separates valid and rejected records, and loads clean data into PostgreSQL using idempotent batch upserts.

The project demonstrates practical Data Engineering fundamentals including ingestion, schema validation, record-level data quality, PostgreSQL modeling, batch processing, idempotency, observability, automated testing, Docker-based infrastructure, SQL analytics, and Continuous Integration.

---

## Architecture

```text
DummyJSON REST API
        │
        ▼
     Ingestion
        │
        ▼
   RAW Snapshots
        │
        ▼
Envelope Validation
        │
        ▼
 Record Validation
        │
        ├──────────────► Rejected Records
        │
        ▼
   Clean Products
        │
        ▼
PostgreSQL Batch Load
        │
        ▼
UPSERT / Idempotency
        │
        ▼
   Analytics SQL


Operational Metadata

Pipeline Execution
        │
        ▼
   pipeline_runs
        │
        ├── RUNNING
        ├── SUCCESS
        └── FAILED
```

---

## Data Pipeline

The pipeline follows this lifecycle:

```text
Source
→ Ingestion
→ Raw
→ Validation
→ Clean / Rejected
→ PostgreSQL
→ Analytics
→ Monitoring
```

Each execution:

1. Retrieves product data from DummyJSON.
2. Stores the original API response as a timestamped RAW snapshot.
3. Validates the API payload structure.
4. Validates each product record independently.
5. Collects multiple validation errors per invalid record.
6. Separates valid and rejected records.
7. Stores clean records as JSON.
8. Loads valid products into PostgreSQL.
9. Uses PostgreSQL UPSERT logic to make repeated runs idempotent.
10. Records execution status and metrics in `pipeline_runs`.

---

## Data Quality

RetailPulse validates data at two levels.

### Payload-level validation

The source payload must contain:

- `products`
- `total`
- `skip`
- `limit`

A source schema mismatch stops downstream processing.

### Record-level validation

Required product fields:

- `id`
- `title`
- `category`
- `price`
- `stock`
- `sku`

The validator also checks:

- expected data types;
- empty strings;
- negative prices;
- negative stock;
- missing required fields.

Invalid records can contain multiple validation errors without stopping validation of the rest of the batch.

---

## PostgreSQL Model

### `products`

Stores validated product records.

Important constraints include:

- `product_id` as Primary Key;
- unique `sku`;
- mandatory core fields;
- non-negative `price`;
- non-negative `stock`;
- load timestamp.

### `pipeline_runs`

Stores operational metadata for each pipeline execution.

It records:

- execution ID;
- pipeline name;
- start timestamp;
- finish timestamp;
- status: `RUNNING`, `SUCCESS`, or `FAILED`;
- extracted rows;
- valid rows;
- rejected rows;
- loaded rows;
- RAW file path;
- clean file path;
- rejected file path;
- error message.

This allows pipeline executions to be audited and failures to be diagnosed.

---

## Idempotency

Product loading uses PostgreSQL UPSERT behavior:

```sql
ON CONFLICT (product_id)
DO UPDATE
```

Reprocessing the same source data therefore does not create duplicate product records.

Existing products are updated while new products are inserted.

Example:

```text
First execution  → 194 products
Second execution → 194 products
```

instead of:

```text
388 products
```

---

## Observability

Every pipeline execution receives a `run_id`.

The pipeline records:

```text
RUNNING
   ↓
pipeline processing
   ↓
SUCCESS
```

or, when an exception occurs:

```text
RUNNING
   ↓
pipeline failure
   ↓
FAILED
   ↓
error_message
```

Partial execution metrics are preserved so failures can be inspected after execution.

Example:

```text
rows_extracted = 194
rows_valid     = 194
rows_rejected  = 0
rows_loaded    = 194
status         = SUCCESS
```

---

## Analytics

The project includes SQL queries for:

- total products;
- total categories;
- average product price;
- total stock;
- products per category;
- average price by category;
- stock by category;
- highest-value inventory products;
- inventory value by category.

Analytics queries are located in:

```text
sql/analytics/
```

---

## Testing

RetailPulse uses `pytest`.

The test suite includes:

- valid payload validation;
- missing source schema fields;
- multiple validation errors per product;
- valid product records;
- PostgreSQL batch insertion;
- PostgreSQL UPSERT behavior;
- database cleanup after integration tests.

Run:

```bash
python3 -m pytest
```

---

## Docker

PostgreSQL can be provisioned using Docker Compose.

The container automatically initializes the database schema using:

```text
sql/ddl/001_create_products.sql
sql/ddl/002_create_pipeline_runs.sql
```

Start PostgreSQL:

```bash
docker compose up -d
```

Check container health:

```bash
docker compose ps
```

Stop the infrastructure:

```bash
docker compose down
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/georgerodriguez2000/retailpulse.git
cd retailpulse
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Default Docker configuration:

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=retailpulse
DB_USER=retailpulse
DB_PASSWORD=retailpulse_dev
```

### 5. Start PostgreSQL

```bash
docker compose up -d
```

### 6. Run the pipeline

```bash
python3 -m src.ingestion.products_api
```

A successful execution should produce output similar to:

```text
Payload Validation: OK
Productos extraidos: 194
Productos validos: 194
Productos rechazados: 0
Productos cargados en PostgreSQL: 194
```

The exact number of products may change if the upstream source changes.

---

## Running Analytics

```bash
PGPASSWORD=retailpulse_dev psql \
  -h localhost \
  -p 5433 \
  -U retailpulse \
  -d retailpulse \
  -f sql/analytics/product_metrics.sql
```

---

## Continuous Integration

GitHub Actions automatically:

1. provisions PostgreSQL 17;
2. installs Python dependencies;
3. initializes the database schema;
4. runs the complete pytest suite.

This verifies that RetailPulse can be reconstructed and tested outside the original development machine.

---

## Project Structure

```text
retailpulse/
│
├── data/
│   ├── raw/
│   ├── clean/
│   └── rejected/
│
├── sql/
│   ├── ddl/
│   │   ├── 001_create_products.sql
│   │   └── 002_create_pipeline_runs.sql
│   │
│   └── analytics/
│       └── product_metrics.sql
│
├── src/
│   ├── ingestion/
│   ├── validation/
│   ├── loading/
│   └── monitoring/
│
├── tests/
│
├── .github/
│   └── workflows/
│
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Engineering Decisions

### Batch processing instead of streaming

The dataset and use case do not require real-time processing.

Batch ingestion provides sufficient value with substantially lower infrastructure and operational complexity.

### PostgreSQL as the primary database

PostgreSQL is sufficient for the current workload and allows the project to demonstrate:

- relational modeling;
- constraints;
- SQL;
- transactions;
- UPSERT operations;
- analytics;
- operational metadata.

### No Kafka, Spark, or Kubernetes

These technologies were intentionally excluded because they would add complexity without solving a current project requirement.

### Raw source preservation

Original API responses are preserved before transformation to support:

- debugging;
- auditing;
- reprocessing;
- investigation of upstream schema changes.

### Validation before database loading

Only records that pass Data Quality validation are loaded into the operational database.

### Database-level constraints

Data validation is enforced both in Python and PostgreSQL.

This provides an additional protection layer if invalid data bypasses application-level validation.

---

## Skills Demonstrated

- Python
- REST API ingestion
- JSON processing
- ETL / Data Pipelines
- Data Quality
- Schema Validation
- Record Validation
- PostgreSQL
- SQL
- Data Modeling
- Constraints
- Batch Processing
- Transactions
- UPSERT
- Idempotency
- Operational Metadata
- Pipeline Observability
- Error Handling
- pytest
- Unit Testing
- Integration Testing
- Docker Compose
- Git
- GitHub
- GitHub Actions
- Continuous Integration
- Technical Documentation

---

## Purpose

RetailPulse is a portfolio project built to demonstrate practical Data Engineering skills through a working, testable, observable, and reproducible data pipeline rather than through isolated notebooks or academic exercises.