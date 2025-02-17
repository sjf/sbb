#!/bin/bash
set -uxe

git pull
# Rebuild all containers, use cached layers
docker compose build
docker compose up --no-deps -d --wait backend || dlogs backend
# Regenerate static site
./update.sh generator

export BACKEND=https://beekey.buzz
pytest e2e_test.py
