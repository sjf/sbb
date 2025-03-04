#!/bin/bash
set -u

mkdir -p scraped/
cp -v test-data/*.json scraped/
if [[ ! -f data/requests_cache.sqlite ]]; then
  cp -v test-data/requests_cache.sqlite data/
fi
