#!/bin/bash
set -ux

DEV=${DEV:-True}

# cd site
# httpserver_w_headers.py &
# cd ..
. .venv/bin/activate

export DOMAIN=http://box:8081
export FULL=True
export IGNORE_MISSING=True
export DEV

mypy generator.py && ./generator.py || true
date

while inotifywait -r -e modify,create,delete templates/ static_files/ *.py *.ini *.js; do
 mypy generator.py && update.sh generator || true;
 date
 echo "-----------------------------------------------------------"
 sleep 1s
done
