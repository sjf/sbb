#!/bin/bash
set -eux

DEV=${DEV:-True}

# cd site
# httpserver_w_headers.py &
# cd ..
. .venv/bin/activate

export DOMAIN=http://box:8081
export DEV

mypy generator.py && ./generator.py || true
date

while inotifywait -r -e modify,create,delete templates/ static/ *.py *.ini; do
 mypy generator.py && ./generator.py || true;
 date
 echo "-----------------------------------------------------------"
 sleep 1s
done
