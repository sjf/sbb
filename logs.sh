#!/bin/bash
set -xue
export DEST=~/logs/ 
~/scripts/goaccess.sh -v ~/logs/sbb-nginx-access.log*
