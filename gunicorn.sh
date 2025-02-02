#!/bin/bash
set -eux
# Start local dev gunicorn server.

# activate python virtual env
. .venv/bin/activate

PORT=8002
LOG_DIR=/tmp/logs

export FLASK_ENV=development
export ELASTIC_API_KEY_FILE=secrets/elastic-api-key.txt
export PYUTILS_LOG_DIR=$LOG_DIR


# reload srcs on change
# in access log, use remote address instead of real-ip header b/c the header is not set by gunicorn.
gunicorn \
  -c gunicorn_config_dev.py \
  --reload \
  --log-level=INFO \
  --access-logformat='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' \
  --access-logfile=$LOG_DIR/gunicorn-access.log \
  --error-logfile=$LOG_DIR/gunicorn-error.log \
  -b 0.0.0.0:$PORT app:app


