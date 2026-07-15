FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml README.md ./
COPY app ./app
COPY agents ./agents
COPY mcp_server ./mcp_server
RUN pip install --upgrade pip \
    && pip install '.[ai,observability]' \
    && mkdir -p /app/data/chroma /app/data/policies \
    && chown -R app:app /app/data

USER app
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
