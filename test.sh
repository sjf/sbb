#!/bin/bash
set -eux
export PYTEST=1
pytest --mypy --ignore=external-scripts $@
