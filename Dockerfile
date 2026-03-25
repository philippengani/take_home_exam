FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY . .

RUN uv sync --frozen --no-dev


FROM base AS member-data

CMD ["uv", "run", "uvicorn", "mock_api.member_data:app", "--host", "0.0.0.0", "--port", "8001"]


FROM base AS product-info

CMD ["uv", "run", "uvicorn", "mock_api.product_info:app", "--host", "0.0.0.0", "--port", "8002"]


FROM base AS pricing-ml-model

CMD ["uv", "run", "uvicorn", "mock_api.pricing_ml_model:app", "--host", "0.0.0.0", "--port", "8003"]


FROM base AS audit-log

CMD ["uv", "run", "uvicorn", "mock_api.audit_log:app", "--host", "0.0.0.0", "--port", "8004"]


FROM base AS pricing-service

CMD ["uv", "run", "uvicorn", "pricer_service.main:app", "--host", "0.0.0.0", "--port", "8005"]
