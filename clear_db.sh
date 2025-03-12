#!/bin/bash
set -u
set -x

rm -f data/nyt.db
# rm -rf site/*
elasticsearch/clear.sh
elasticsearch/setup_indexes.sh
