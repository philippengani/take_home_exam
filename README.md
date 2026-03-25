# ML Pricing Service

This repository contains the provided mock dependency APIs and a new pricing service that orchestrates them with low-latency async calls.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Install

```bash
uv sync --locked --all-groups
```

## Run With Docker

Start all five services with Docker Compose:

```bash
docker compose up --build
```

Call the pricing service from the host:

```bash
curl -X POST http://127.0.0.1:8005/price \
  -H 'Content-Type: application/json' \
  -d '{
    "partner_id": "partner-1",
    "member_id": "member-1",
    "product_id": "BUY"
  }'
```

Stop and remove the containers:

```bash
docker compose down
```

## Run The Mock APIs

Start each mock service in its own terminal:

```bash
uv run uvicorn mock_api.member_data:app --host 127.0.0.1 --port 8001
uv run uvicorn mock_api.product_info:app --host 127.0.0.1 --port 8002
uv run uvicorn mock_api.pricing_ml_model:app --host 127.0.0.1 --port 8003
uv run uvicorn mock_api.audit_log:app --host 127.0.0.1 --port 8004
```

Run the pricing service on port `8005`:

```bash
uv run uvicorn pricer_service.main:app --host 127.0.0.1 --port 8005
```

## Example Request

```bash
curl -X POST http://127.0.0.1:8005/price \
  -H 'Content-Type: application/json' \
  -d '{
    "partner_id": "partner-1",
    "member_id": "member-1",
    "product_id": "BUY"
  }'
```

## Quality Checks

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run python -m mypy
uv run python -m pytest -q
```

## Latency Notes

The service keeps the response path lean by:

- member and product lookups run in parallel via `asyncio.gather`
- audit logging is scheduled after the response path, so it does not block pricing responses
- outbound requests use a short configurable timeout to fail fast on slow upstreams

Validate the assignment's `<300ms` latency target with a benchmark run against the local stack:

```bash
uv run python scripts/measure_price_latency.py
```

## Configuration

The pricing service reads these optional environment variables:

- `MEMBER_DATA_URL`
- `PRODUCT_INFO_URL`
- `PRICING_MODEL_URL`
- `AUDIT_LOG_URL`
- `REQUEST_TIMEOUT_SECONDS`
