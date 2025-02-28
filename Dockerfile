# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

# Copy this first so it is a separate layer and can be cached.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -q -r requirements.txt

# Ensure the css file was created first.
COPY out.css /app/out.css
COPY . /app
WORKDIR /app

CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
# CMD ["tail", "-f", "/dev/null"]
