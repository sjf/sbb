#!/bin/bash
set -u

mkdir -p scraped/
mkdir -p data/
cp -v test-data/*.json scraped/
if [[ ! -f data/requests_cache.sqlite ]]; then
  cp -v test-data/requests_cache.sqlite data/
fi
