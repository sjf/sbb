#!/bin/bash
set -ue

. $(dirname $0)/utils.sh

jcurl DELETE "/$INDEX1"
