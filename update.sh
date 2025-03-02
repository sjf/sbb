#!/bin/bash
set -ue

cd ~/sbb
if [ ! -f .venv/bin/activate ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip3 install -qr requirements.txt

export PYUTILS_LOG_DIR=$HOME/logs
export PYUTILS_LOG_FILE=sbb.log

CMD=${1:-all}
shift
if [[ $CMD == 'all' ]]; then
  ./scraper.py
  ./importer.py
  ./generator.py
elif [[ $CMD == 'github' ]]; then
  ./importer.py
  ./generator.py
elif [[ $CMD == 'generator' ]]; then
  ./generator.py
elif [[ $CMD == 'e2e' ]]; then
  pytest e2e_test.py "$@"
fi
