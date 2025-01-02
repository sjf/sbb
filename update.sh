#!/bin/bash
set -uex

cd ~/sbb
if [ ! -f .venv/bin/activate ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip3 install -r requirements.txt

export MB_LOG_DIR=/home/sjf/logs
export MB_LOG_FILE=sbb.log

./scraper.py
./importer.py
./generator.py
