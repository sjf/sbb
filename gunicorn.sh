#!/bin/bash
set -eux
# Start local dev gunicorn server.

# activate python virtual env
. .venv/bin/activate

export FLASK_ENV=development
export ELASTIC_API_KEY_FILE=secrets/elastic-api-key.txt
export MB_LOG_DIR=/home/sjf/logs

# reload srcs on change
# in access log, use remote address instead of real-ip header b/c the header is not set by gunicorn.
gunicorn \
  -c gunicorn_config_dev.py \
  --reload \
  --log-level=INFO \
  --access-logformat='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' \
  --access-logfile=$MB_LOG_DIR/gunicorn-access.log \
  --error-logfile=$MB_LOG_DIR/gunicorn-error.log \
  -b 0.0.0.0:8001 app:app


