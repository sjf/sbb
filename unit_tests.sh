#!/bin/bash
set -eu

# Remove mac dot files.
find . -name ._\*  -type f -print0 | xargs -0 -r rm -v
pytest --mypy --ignore=e2e_test.py --ignore=external-scripts $@
