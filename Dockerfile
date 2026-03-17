FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/app/src

WORKDIR /app

COPY requirements.txt requirements-dev.txt pyproject.toml README.md ./
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

COPY . .

EXPOSE 8000 8501

CMD ["uvicorn", "procurement_spend_analysis.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
