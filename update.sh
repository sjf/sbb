#!/bin/bash
set -ue

if [[ -n "${GITHUB_RUN_ID:-}" ]]; then
  cd ~/work/sbb/sbb
else
  cd ~/sbb
fi

# Use globally installed node modules.
export NODE_PATH=$(npm root -g)

if [ ! -f .venv/bin/activate ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip3 install -qr requirements.txt

export PYUTILS_LOG_DIR=$HOME/logs
export PYUTILS_LOG_FILE=sbb.log

if [[ -f pause ]]; then
  echo "Pausing update on $(hostname) because pause file found: $(realpath pause)" >&2
  exit 1
fi

CMD=${1:-all}
shift || true
if [[ $CMD == 'all' ]]; then
  ./scraper.py
  ./importer.py
  ./generator.py
elif [[ $CMD == 'github' ]]; then
  ./setup_testdata.sh
  ./importer.py
  ./generator.py
elif [[ $CMD == 'generator' ]]; then
  ./generator.py
elif [[ $CMD == 'e2e' ]]; then
  pytest e2e_test.py "$@"
fi
