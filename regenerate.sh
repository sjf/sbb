#!/bin/bash
set -uxe

DB=nyt.db
mypy generator.py db.py model.py

rm -rf $DB || true
sqlite3 $DB  < setup.sql

./importer.py

# ./generator.py test-data

#
