#!/bin/bash
set -eux

docker compose up --quiet-pull -d elasticsearch
wait_for_containers.sh 2 60 elasticsearch

## Set up elastic search: create index, api keys, SA token.
elasticsearch/setup_roles.sh

## Create indexes, try to update existing indexes, but this is often not possible.
elasticsearch/setup_indexes.sh


