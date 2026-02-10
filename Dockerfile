FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./

RUN pip install --upgrade pip && \
    pip install \
        alembic>=1.17.2 \
        fastapi>=0.128.0 \
        locust>=2.43.1 \
        passlib[bcrypt]>=1.7.4 \
        psycopg2-binary>=2.9.11 \
        "psycopg[binary]>=3.3.2" \
        "pwdlib[argon2]>=0.3.0" \
        pydantic-settings>=2.12.0 \
        "pydantic[email]>=2.12.5" \
        python-dotenv>=1.2.1 \
        "python-jose[cryptography]>=3.5.0" \
        python-multipart>=0.0.21 \
        redis>=7.1.0 \
        requests>=2.32.5 \
        slowapi>=0.1.9 \
        sqlalchemy>=2.0.45 \
        uvicorn>=0.40.0

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini main.py ./

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]