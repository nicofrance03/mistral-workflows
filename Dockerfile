FROM python:3.12-slim

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --no-cache-dir mistralai-workflows "mistralai>=3.0.0" "httpx>=0.27.0"

COPY src ./src

CMD ["python", "-m", "src.entrypoints.worker"]
