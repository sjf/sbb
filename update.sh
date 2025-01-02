#!/bin/bash
set -uex

cd ~/sbb
. .venv/bin/activate

export MB_LOG_DIR=.
export MB_LOG_FILE=scraper.log

./scraper.py
./importer.py
./generator.py
