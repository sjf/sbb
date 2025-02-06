#!/bin/bash
set -eu
cd ~/sbb
. .venv/bin/activate

export PYUTILS_LOG_DIR=.
export PYUTILS_LOG_FILE=scraper.log

./scraper.py
