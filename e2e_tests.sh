#!/bin/bash
set -eux

if [[ $(hostname) == 'box' ]]; then
  export VERIFY_SSL=False
elif [[ $(hostname) == 'nytspellingbeesolver.com' ]]; then
  export BACKEND=https://beekey.buzz
fi
pytest e2e_test.py "$@"
