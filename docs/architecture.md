# RetailPulse Architecture

## Overview

RetailPulse is a batch-oriented Data Engineering pipeline designed to ingest product data from a public REST API, preserve the original source payload, validate data quality, separate valid and rejected records, load validated data into PostgreSQL, and expose operational and analytical information.

The architecture intentionally favors simplicity, reproducibility, and observability over distributed-system complexity.

---

## High-Level Architecture

```text
                    ┌──────────────────────┐
                    │   DummyJSON API      │
                    │   Public REST API    │
                    └──────────┬───────────┘
                               │
                               │ HTTP GET
                               ▼
                    ┌──────────────────────┐
                    │      Ingestion       │
                    │   products_api.py    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    RAW Snapshot      │
                    │   Timestamped JSON   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Envelope Validation  │
                    │ Source Schema Check  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Record Validation   │
                    │  Data Quality Rules  │
                    └──────────┬───────────┘
                               │
                     ┌─────────┴─────────┐
                     │                   │
                     ▼                   ▼
          ┌──────────────────┐  ┌──────────────────┐
          │  Valid Products  │  │ Rejected Records │
          │    Clean JSON    │  │ Errors + Record  │
          └────────┬─────────┘  └──────────────────┘
                   │
                   ▼
          ┌──────────────────────┐
          │ PostgreSQL Batch Load│
          │       psycopg        │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ UPSERT / Idempotency │
          │ ON CONFLICT UPDATE   │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │      PostgreSQL      │
          │                      │
          │ products             │
          │ pipeline_runs        │
          └──────────┬───────────┘
                     │
          ┌──────────┴───────────┐
          │                      │
          ▼                      ▼
┌──────────────────┐   ┌──────────────────────┐
│  Analytics SQL   │   │   Observability      │
│ product_metrics  │   │ RUNNING / SUCCESS /  │
│                  │   │ FAILED + metrics     │
└──────────────────┘   └──────────────────────┘
```

---

## Main Components

### 1. Ingestion Layer

Location:

```text
src/ingestion/
```

Primary module:

```text
products_api.py
```

Responsibilities:

- connect to the public REST API;
- retrieve product data;
- parse the JSON response;
- coordinate pipeline execution;
- preserve RAW snapshots;
- trigger validation;
- trigger PostgreSQL loading;
- update pipeline execution metadata.

The ingestion layer acts as the orchestration point for the current pipeline.

---

## 2. RAW Layer

Location:

```text
data/raw/products/
```

Purpose:

Preserve the original source payload before transformation.

RAW snapshots support:

- debugging;
- auditing;
- source-change investigation;
- reprocessing;
- reproducibility.

Each execution creates a timestamped JSON snapshot.

Example:

```text
products_20260923_140000.json
```

RAW preservation does not imply that the data is valid.

Validation determines whether the data is allowed to continue through the pipeline.

---

## 3. Validation Layer

Location:

```text
src/validation/
```

Primary module:

```text
products_validator.py
```

Validation is divided into two levels.

### Envelope Validation

Checks whether the API response satisfies the expected source contract.

Required payload keys:

```text
products
total
skip
limit
```

If the source structure changes unexpectedly, downstream processing stops.

### Record-Level Validation

Each product is validated independently.

Required fields:

```text
id
title
category
price
stock
sku
```

Validation also checks:

- data types;
- missing fields;
- empty strings;
- negative price values;
- negative stock values.

Record validation accumulates multiple errors for the same product instead of stopping at the first error.

---

## 4. Clean and Rejected Layers

Validated products are divided into two groups.

### Clean

Location:

```text
data/clean/products/
```

Contains records that passed Data Quality validation.

Only validated records are eligible for database loading.

### Rejected

Location:

```text
data/rejected/products/
```

Contains invalid records together with their validation errors.

Conceptually:

```text
Source Batch
     │
     ▼
Validation
     │
 ┌───┴────┐
 │        │
 ▼        ▼
Valid   Rejected
```

This design prevents one defective product from stopping validation of the entire batch.

---

## 5. Loading Layer

Location:

```text
src/loading/
```

Primary module:

```text
postgres.py
```

Responsibilities:

- establish PostgreSQL connections;
- load validated products;
- execute batch inserts;
- manage transactions;
- perform UPSERT operations.

The loader uses one database connection and transaction for a batch instead of opening a new connection for every product.

---

## 6. PostgreSQL

PostgreSQL stores both business data and operational metadata.

### `products`

Stores validated product data.

Important database rules include:

```text
product_id
→ PRIMARY KEY

sku
→ UNIQUE

price
→ CHECK >= 0

stock
→ CHECK >= 0

core fields
→ NOT NULL
```

Application-level validation and database constraints provide two independent protection layers.

---

### `pipeline_runs`

Stores metadata about pipeline executions.

Tracked information includes:

```text
run_id
pipeline_name
started_at
finished_at
status
rows_extracted
rows_valid
rows_rejected
rows_loaded
raw_file
clean_file
rejected_file
error_message
```

Possible states:

```text
RUNNING
SUCCESS
FAILED
```

This table provides operational observability and historical execution information.

---

## 7. Idempotency

Loading uses PostgreSQL UPSERT behavior:

```sql
ON CONFLICT (product_id)
DO UPDATE
```

The same source dataset can therefore be processed repeatedly without duplicating product records.

Example:

```text
Execution 1
194 source products
→ 194 database products

Execution 2
same 194 source products
→ still 194 database products
```

Changed products are updated.

New products are inserted.

---

## 8. Error Handling

The pipeline execution is wrapped in Python exception handling.

Conceptually:

```text
Start pipeline run
        │
        ▼
       TRY
        │
        ├── Fetch
        ├── RAW
        ├── Validate
        ├── Clean
        └── Load
        │
        ▼
     SUCCESS
```

If an exception occurs:

```text
Exception
   │
   ▼
FAILED
   │
   ├── partial metrics
   └── error_message
```

The exception is registered in PostgreSQL and then re-raised so the original traceback remains available for debugging.

---

## 9. Analytics Layer

Location:

```text
sql/analytics/
```

Primary file:

```text
product_metrics.sql
```

The analytics layer demonstrates SQL operations over validated PostgreSQL data.

It includes:

- aggregations;
- `GROUP BY`;
- `COUNT`;
- `AVG`;
- `SUM`;
- derived metrics;
- sorting;
- Top-N queries.

Examples include:

```text
products per category
average price by category
total stock by category
inventory value
highest-value inventory products
```

---

## 10. Testing

Location:

```text
tests/
```

Testing includes two categories.

### Unit / Data Quality Tests

Validate deterministic Python logic such as:

- valid source payloads;
- missing schema fields;
- valid product records;
- multiple validation errors.

### PostgreSQL Integration Test

Validates interaction between:

```text
Python
→ psycopg
→ PostgreSQL
```

The integration test verifies:

- batch insertion;
- persisted records;
- UPSERT behavior;
- updated values;
- cleanup after execution.

---

## 11. Docker Infrastructure

Infrastructure is defined in:

```text
docker-compose.yml
```

Docker Compose provisions:

```text
PostgreSQL 17
database: retailpulse
user: retailpulse
persistent volume
healthcheck
DDL initialization
```

The host uses:

```text
localhost:5433
```

while PostgreSQL inside the container runs on:

```text
5432
```

The different host port avoids conflict with a locally installed PostgreSQL instance.

---

## Automatic Schema Initialization

Docker mounts:

```text
sql/ddl/001_create_products.sql
sql/ddl/002_create_pipeline_runs.sql
```

into:

```text
/docker-entrypoint-initdb.d/
```

When PostgreSQL initializes a new volume, these scripts automatically create the required schema.

Therefore:

```bash
docker compose up -d
```

is sufficient to provision the project database structure on a clean environment.

---

## 12. Continuous Integration

Workflow:

```text
.github/workflows/tests.yml
```

GitHub Actions runs the project in an external environment.

The workflow:

```text
Checkout repository
        ↓
Start PostgreSQL 17
        ↓
Install Python
        ↓
Install dependencies
        ↓
Initialize database schema
        ↓
Run pytest
```

This verifies that the project is reproducible outside the original development machine.

---

## Architectural Principles

### Simplicity

The architecture intentionally avoids unnecessary distributed-system components.

No:

```text
Kafka
Spark
Kubernetes
Microservices
```

The current workload does not justify them.

---

### Separation of Responsibilities

```text
ingestion
→ source acquisition and orchestration

validation
→ Data Quality

loading
→ PostgreSQL persistence

monitoring
→ operational metadata

sql
→ schema and analytics

tests
→ automated verification
```

---

### Defense in Depth

Data integrity is enforced in multiple layers.

```text
Python validation
        +
PostgreSQL constraints
```

If application validation fails to catch a defect, database constraints provide an additional protection layer.

---

### Reproducibility

The project includes:

```text
requirements.txt
.env.example
Docker Compose
DDL scripts
GitHub Actions
```

to minimize machine-specific configuration.

---

### Observability

A successful pipeline is not defined only by whether data appears in PostgreSQL.

RetailPulse also records:

```text
what happened
when it happened
how many records were processed
how many were rejected
whether loading completed
where generated files are located
why an execution failed
```

---

## Current Scope

RetailPulse is intentionally focused on one product-data pipeline.

The current architecture demonstrates the complete lifecycle:

```text
Source
→ Ingestion
→ Raw
→ Data Quality
→ Clean / Rejected
→ PostgreSQL
→ Analytics
→ Monitoring
→ Testing
→ CI
```

The architecture can be extended with additional entities or sources if a future requirement justifies the added complexity.