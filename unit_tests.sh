#!/bin/bash
set -eux
export PYTEST=1
pytest --mypy --ignore=e2e_test.py  --ignore=external-scripts $@
