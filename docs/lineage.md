# RetailPulse Data Lineage

## Overview

RetailPulse tracks how product data moves from the upstream source through ingestion, validation, persistence, and analytics.

The goal of lineage is to answer:

> Where did this data come from, what happened to it, and where is it stored now?

---

## End-to-End Lineage

```text
DummyJSON REST API
        │
        ▼
HTTP Response
        │
        ▼
JSON Parsing
        │
        ▼
products_data
        │
        ├──────────────► RAW Snapshot
        │                data/raw/products/
        │
        ▼
Envelope Validation
        │
        ▼
products_data["products"]
        │
        ▼
Record Validation
        │
        ├──────────────► rejected_products
        │                data/rejected/products/
        │
        ▼
valid_products
        │
        ├──────────────► Clean Snapshot
        │                data/clean/products/
        │
        ▼
PostgreSQL Batch Loader
        │
        ▼
UPSERT
        │
        ▼
products table
        │
        ▼
Analytics SQL
        │
        ▼
Business Metrics
```

Operational lineage is tracked in parallel:

```text
Pipeline Start
      │
      ▼
pipeline_runs
status = RUNNING
      │
      ▼
Pipeline Processing
      │
      ├── rows_extracted
      ├── rows_valid
      ├── rows_rejected
      ├── rows_loaded
      ├── raw_file
      ├── clean_file
      └── rejected_file
      │
      ▼
SUCCESS / FAILED
```

---

## 1. Source

Source:

```text
DummyJSON Products REST API
```

Endpoint:

```text
https://dummyjson.com/products?limit=0
```

The API returns a JSON payload with the expected envelope:

```text
products
total
skip
limit
```

The `products` key contains the product records processed by RetailPulse.

---

## 2. Ingestion

Module:

```text
src/ingestion/products_api.py
```

The ingestion layer:

1. sends the HTTP request;
2. verifies the HTTP response status;
3. parses the JSON response;
4. stores the resulting Python object in memory;
5. preserves the source response as RAW data.

Conceptually:

```text
HTTP Response
     │
     ▼
response.json()
     │
     ▼
products_data
```

At this stage no business transformation has been applied.

---

## 3. RAW Data

Location:

```text
data/raw/products/
```

Each pipeline execution produces a timestamped RAW snapshot.

Example:

```text
products_20260923_140000.json
```

RAW data represents the source payload before record-level cleaning or transformation.

Purpose:

- preserve source evidence;
- support debugging;
- investigate source schema changes;
- enable reprocessing;
- provide auditability.

A RAW snapshot can exist even if later validation fails.

---

## 4. Envelope Validation

Module:

```text
src/validation/products_validator.py
```

The first Data Quality stage validates the structure of the source payload.

Required keys:

```text
products
total
skip
limit
```

Example flow:

```text
products_data
      │
      ▼
validate_products_payload()
      │
      ├── valid schema
      │      ▼
      │   continue
      │
      └── schema mismatch
             ▼
          pipeline failure
```

If the upstream provider changes the source contract unexpectedly, the pipeline records the execution as failed instead of silently processing an unknown structure.

---

## 5. Product Extraction

After the envelope is validated:

```python
products_data["products"]
```

selects the product list from the full payload.

Conceptually:

```text
products_data
│
├── products ─────────► product list
├── total
├── skip
└── limit
```

Each element of the `products` list is a product record represented as a Python dictionary.

---

## 6. Record-Level Validation

Each product is processed through:

```text
validate_product_record()
```

Required product fields:

```text
id
title
category
price
stock
sku
```

Additional Data Quality checks include:

```text
type validation
empty-string detection
non-negative price
non-negative stock
missing required fields
```

Multiple validation errors can be collected for the same record.

Example:

```text
Product
│
├── title = ""
├── price = -50
└── stock = -3

        ↓

Validation Errors

[
  "title cannot be empty",
  "price cannot be negative",
  "stock cannot be negative"
]
```

---

## 7. Valid / Rejected Split

The batch validator separates records into:

```text
valid_products
rejected_products
```

Flow:

```text
Product Batch
     │
     ▼
Validation
     │
 ┌───┴──────────────┐
 │                  │
 ▼                  ▼
Valid              Invalid
 │                  │
 ▼                  ▼
valid_products     rejected_products
```

Rejected records retain:

```text
original product
+
validation errors
```

This preserves the context required to diagnose Data Quality failures.

---

## 8. Clean Layer

Location:

```text
data/clean/products/
```

Only records that pass validation are written to the clean layer.

Example:

```text
products_clean_20260923_140000.json
```

The clean dataset becomes the approved input for PostgreSQL loading.

Conceptually:

```text
RAW
 ↓
Validation
 ↓
Clean
```

No rejected record is intentionally loaded into PostgreSQL.

---

## 9. Rejected Layer

Location:

```text
data/rejected/products/
```

Rejected data is only written when invalid records exist.

Each rejected item preserves:

```text
source record
validation errors
```

This layer supports:

- investigation;
- remediation;
- Data Quality analysis;
- future reprocessing.

---

## 10. PostgreSQL Loading

Module:

```text
src/loading/postgres.py
```

Input:

```text
valid_products
```

The loading layer converts product dictionary values into parameterized SQL statements.

Example mapping:

```text
Source / Python        PostgreSQL

id                  → product_id
sku                 → sku
title               → title
category            → category
brand               → brand
price               → price
stock               → stock
rating              → rating
```

The loader uses parameterized SQL through psycopg.

This avoids building SQL statements through direct string interpolation.

---

## 11. PostgreSQL Product Table

Destination:

```text
products
```

The table represents the validated operational state of product data.

Important constraints include:

```text
product_id
→ PRIMARY KEY

sku
→ UNIQUE

price
→ CHECK price >= 0

stock
→ CHECK stock >= 0

required fields
→ NOT NULL
```

This creates a second Data Quality protection layer after Python validation.

---

## 12. UPSERT and Idempotency

The loader uses:

```sql
ON CONFLICT (product_id)
DO UPDATE
```

Lineage behavior:

```text
New product
     │
     ▼
INSERT
```

or:

```text
Existing product
     │
     ▼
UPDATE
```

Repeated processing of the same source dataset does not create duplicate product rows.

This allows a RAW dataset to be safely reprocessed.

---

## 13. Load Metadata

The `products` table includes:

```text
loaded_at
```

This timestamp represents when RetailPulse last loaded or updated the record.

It is distinct from source-generated metadata.

Conceptually:

```text
source information
        +
RetailPulse load timestamp
```

---

## 14. Pipeline Execution Lineage

Table:

```text
pipeline_runs
```

Every execution receives a unique:

```text
run_id
```

At pipeline start:

```text
status = RUNNING
```

The same row is later updated to:

```text
SUCCESS
```

or:

```text
FAILED
```

The execution record contains:

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

---

## 15. Successful Execution Example

Conceptually:

```text
run_id = 17
        │
        ├── Source API
        │
        ├── rows_extracted = 194
        │
        ├── RAW snapshot
        │
        ├── rows_valid = 194
        │
        ├── rows_rejected = 0
        │
        ├── Clean snapshot
        │
        ├── PostgreSQL load
        │
        ├── rows_loaded = 194
        │
        └── status = SUCCESS
```

This provides operational traceability from execution to generated artifacts and loaded data.

---

## 16. Failed Execution Example

If a failure occurs after RAW persistence:

```text
run_id = 18
        │
        ├── rows_extracted = 194
        ├── raw_file = ...
        ├── rows_valid = 0
        ├── rows_loaded = 0
        ├── status = FAILED
        └── error_message = ...
```

This allows investigation of the exact source payload associated with the failed execution.

---

## 17. Analytics Lineage

Analytics queries are stored in:

```text
sql/analytics/product_metrics.sql
```

The analytical lineage is:

```text
DummyJSON
    ↓
RAW
    ↓
Validated Products
    ↓
PostgreSQL products
    ↓
SQL Aggregations
    ↓
Metrics
```

Examples:

```text
products.price
      │
      ▼
AVG(price)
      │
      ▼
average_price
```

and:

```text
products.price
      +
products.stock
      │
      ▼
price * stock
      │
      ▼
inventory_value
```

---

## 18. Lineage Boundaries

RetailPulse currently provides lineage at the pipeline-execution and dataset level.

It can answer:

```text
What source was used?
What RAW payload was created?
How many records were extracted?
How many passed validation?
How many were rejected?
What clean dataset was generated?
How many records were loaded?
Did the execution succeed?
What error caused a failure?
What database table consumes the clean data?
What source columns contribute to analytical metrics?
```

The project does not currently implement a dedicated enterprise lineage platform or column-level lineage engine.

That complexity is not required for the current scope.

---

## Summary

RetailPulse lineage can be represented as:

```text
Source
  ↓
RAW
  ↓
Envelope Validation
  ↓
Record Validation
  ↓
Clean / Rejected
  ↓
PostgreSQL
  ↓
UPSERT
  ↓
Analytics
```

with execution metadata tracked through:

```text
pipeline_runs
```

This makes the pipeline traceable, auditable, debuggable, and safe to reprocess.