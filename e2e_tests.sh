#!/bin/bash
set -eux
export PYTEST=1
pytest e2e_test.py $@
