#!/bin/bash
set -eux

# cd site
# httpserver_w_headers.py &
# cd ..
. .venv/bin/activate

export DOMAIN=http://box:8081
export DEV=1

mypy generator.py && ./generator.py || true

while inotifywait -r -e modify,create,delete \
templates/ \
static/ \
generator.py \
model.py \
db.py \
; do
  sleep 1s
  mypy generator.py && ./generator.py || true;
 echo "-----------------------------------------------------------"
done
