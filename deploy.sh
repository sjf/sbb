#!/bin/bash
set -uxe

cd ~/sbb
git pull

# Rebuild all containers, use cached layers
docker compose build --quiet backend
docker compose up --no-deps -d --wait backend || dlogs backend
# Regenerate static site
./update.sh generator

export BACKEND=https://beekey.buzz
./update.sh e2e
