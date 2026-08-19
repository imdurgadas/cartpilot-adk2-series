# Part 14 — Cloud Run deployment container.
# ADK's own `adk deploy cloud_run` command can build this for you
# automatically from source; this Dockerfile is here for when you want
# an explicit, version-controlled build step (e.g. in a CI pipeline)
# instead of the CLI's implicit build-from-source path.
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" cartpilot && \
    chown -R cartpilot:cartpilot /app
COPY . .
USER cartpilot

ENV PATH="/home/cartpilot/.local/bin:$PATH"

CMD ["sh", "-c", "adk api_server --host 0.0.0.0 --port $PORT cartpilot"]
