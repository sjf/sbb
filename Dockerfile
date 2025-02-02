# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

# Copy this first so it is a separate layer and can be cached.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -q -r requirements.txt

WORKDIR /app/backend/
COPY * .

COPY .git/HEAD /tmp/HEAD
COPY .git/FETCH_HEAD /tmp/FETCH_HEAD
RUN /bin/sh -c 'BRANCH=$(rev /tmp/HEAD | cut -d'/' -f1 | rev); HASH=$(grep $BRANCH /tmp/FETCH_HEAD | cut -f1); echo $BRANCH $HASH > git.txt'
RUN date -u +"%d/%b/%Y:%H:%M:%S %z" > build_time.txt

CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
# CMD ["tail", "-f", "/dev/null"]
