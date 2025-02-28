#!/bin/bash
set -uxe

cd ~/sbb
git pull

export FULL=True
# Regenerate static site
./update.sh generator

# Rebuild all containers, use cached layers
docker compose build --quiet backend
docker compose up --no-deps -d --wait backend || dlogs backend


export BACKEND=https://beekey.buzz
./update.sh e2e
