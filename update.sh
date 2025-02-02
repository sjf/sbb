#!/bin/bash
set -uex

cd ~/sbb
if [ ! -f .venv/bin/activate ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip3 install -qr requirements.txt

export PYUTILS_LOG_DIR=$HOME/logs
export PYUTILS_LOG_FILE=sbb.log

./scraper.py
./importer.py
./generator.py
