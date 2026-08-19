# Part 18 — same build as Part 14's Cloud Run container; nothing about
# the image itself is cloud-specific. What changes is how we RUN it
# (docker-compose.yml, below) and where its state lives (self-hosted
# Postgres, not a managed database).
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" cartpilot && \
    chown -R cartpilot:cartpilot /app
COPY . .
USER cartpilot

ENV PATH="/home/cartpilot/.local/bin:$PATH"
EXPOSE 8000

# --session_service_uri points ADK's own DatabaseSessionService at our
# self-hosted Postgres container — no InMemorySessionService, no
# managed cloud database. --no-reload disables the dev auto-reloader,
# which has no place in a long-running container.
CMD ["sh", "-c", "adk api_server --host 0.0.0.0 --port 8000 --session_service_uri \"$SESSION_DB_URL\" --no-reload cartpilot"]
