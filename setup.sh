#!/bin/bash
set -eux

mkdir -p secrets

## Setup flask secret key password
if [ ! -f secrets/flask-secret-key.txt ]; then
  echo Creating Flask secret key...
  uuidgen | tr -d '-' | head -c 12 > secrets/flask-secret-key.txt
fi

## Setup elasticsearch password
if [ ! -f secrets/elastic-password.txt ]; then
  echo Creating elastic password...
  uuidgen | tr -d '-' | head -c 12 > secrets/elastic-password.txt
  # echo -n elastic > secrets/elastic-password.txt
fi
# elasticsearch refuses to start if permissions are not correct.
chmod 600 secrets/elastic-password.txt
# This is required because ES requires a specific owner and permissions
# that make the file unreadable to the host when running in github actions.
cp secrets/elastic-password.txt secrets/elastic-password.txt.orig

## Set up API key
# file has to exist for docker secret binding to work.
touch secrets/elastic-api-key.txt
