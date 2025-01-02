#!/bin/bash
set -uex

cd ~/sbb
. .venv/bin/activate

export MB_LOG_DIR=/home/sjf/logs
export MB_LOG_FILE=sbb.log

./scraper.py
./importer.py
./generator.py
