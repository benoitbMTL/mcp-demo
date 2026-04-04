FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=7000 \
    MCP_TRANSPORT=httpstream \
    MCP_PROTOCOL_VERSION=2025-06-18 \
    WEB_UI_HOST=0.0.0.0 \
    WEB_UI_PORT=7001 \
    WEB_UI_RELOAD=false

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends iputils-ping && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY apps /app/apps
COPY server /app/server
COPY docker/docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 7000 7001

CMD ["/app/docker-entrypoint.sh"]
