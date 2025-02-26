# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

# Copy this first so it is a separate layer and can be cached.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -q -r requirements.txt

COPY . /app
WORKDIR /app

COPY .git/FETCH_HEAD /tmp/FETCH_HEAD
RUN /bin/sh -c 'grep main /tmp/FETCH_HEAD | cut -f1 > git.txt'
RUN date -u +"%d/%b/%Y:%H:%M:%S %z" > build_time.txt

CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
# CMD ["tail", "-f", "/dev/null"]
