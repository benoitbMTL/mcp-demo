FROM python:3.12-slim

# Avoid Python buffering (better logs)
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# System dependencies (needed for ping, PDF, etc.)
RUN apt-get update && \
    apt-get install -y iputils-ping && \
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY server.py /app/server.py
COPY files /app/files

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastmcp \
    pypdf \
    pytz \
    uvicorn

# Expose MCP port
EXPOSE 7000

# Start MCP server (Streamable HTTP)
CMD ["python", "server.py"]
