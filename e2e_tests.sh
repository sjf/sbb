#!/bin/bash
set -eux
export PYTEST=1
if [[ $(hostname) == 'box' ]]; then
  export VERIFY_SSL=False
fi
pytest e2e_test.py $@
