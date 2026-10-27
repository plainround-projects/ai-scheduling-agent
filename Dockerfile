# The sample calendar service as an image: HTTP over SQLite. The agent itself is a command-line program and runs
# from the host's virtual environment (or `docker run ... agent ...` against this service).
FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .
COPY sql ./sql

RUN useradd --system --uid 10001 --home-dir /data app && mkdir /data && chown app /data
USER app
ENV CALENDAR_DB=/data/calendar.db SQL_DIR=/app/sql HTTP_HOST=0.0.0.0 HTTP_PORT=8090

EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/health', timeout=3).status == 200 else 1)"
CMD ["calendar-service", "serve"]
