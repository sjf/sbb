#!/bin/bash
set -x

rm -f nyt.db
rm -rf site/*
elasticsearch/clear.sh
elasticsearch/setup_indexes.sh
