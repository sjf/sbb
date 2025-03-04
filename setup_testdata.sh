#!/bin/bash
set -u

if [[ $(hostname) == 'nytspellingbeesolver.com' ]]; then
  echo 'Not setting up test-data on prod' >&2
  exit 1
fi

mkdir -p scraped/
mkdir -p data/
cp -v test-data/*.json scraped/
if [[ ! -f data/requests_cache.sqlite ]]; then
  cp -v test-data/requests_cache.sqlite data/
fi
