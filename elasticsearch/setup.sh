#!/bin/bash

set -eux

if [ ! -f secrets/elastic-password.txt ]; then
  echo Creating elastic password...
  uuidgen | tr -d '-' | head -c 12 > secrets/elastic-password.txt
fi
# elasticsearch refuses to start if permissions are not correct.
chmod 600 secrets/elastic-password.txt
# This is required because ES requires a specific owner and permissions
# that make the file unreadable to the host when running in github actions.
cp secrets/elastic-password.txt secrets/elastic-password.txt.orig

# file has to exist for docker secret binding to work.
touch secrets/elastic-api-key.txt

docker compose up --quiet-pull -d elasticsearch
wait_for_containers.sh 2 60 elasticsearch

# Set up elastic search: create index, api keys, SA token.
elasticsearch/setup_roles.sh
# Create indexes, try to update existing indexes, but this is often not possible.
elasticsearch/setup_indexes.sh


