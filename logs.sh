#!/bin/bash
set -xue
export DEST=~/logs/ 
goaccess.sh -v ~/logs/sbb-nginx-access.log*
