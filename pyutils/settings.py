#!/usr/bin/env python3
import os
import subprocess
import sys
import time, datetime
import logging
import configparser
import traceback
import re

def load_config(local={}):
  """
  Read config settings from the environment and/or the config file.
  Module specific settings can be set in locals dict.
  Priority is 1. env vars, 2. locals 3. config file
  """
  ini = {}
  config_file = 'config.ini'
  if 'CONFIG_INI' in os.environ:
    config_file = os.environ['CONFIG_INI']
  if not os.path.exists(config_file):
    sys.stderr.write(f"Cannot load config ini: '{config_file}'. File does not exist.\n")
    sys.exit(1)
  ini = _read_ini(config_file)

  result = {}
  for k in ini.keys() | local.keys():
    if k in os.environ:
      result[k] = _from_str(os.environ.get(k))
    elif k in local:
      result[k] = local[k]
    elif k in ini:
      result[k] = _from_str(ini[k])
  return result

def _read_ini(file):
  """ Read an ini file with no section headers. """
  parser = configparser.ConfigParser()
  parser.optionxform = str
  section = 'SECTION'
  with open(file) as fh:
    s = f'[{section}]\n' + fh.read()
  parser.read_string(s)
  return dict(parser[section])

def _from_str(s):
  try:
    return int(s)
  except ValueError:
    pass
  try:
    return float(s)
  except ValueError:
    pass
  if s in ('False', 'false'):
    return False
  if s in ('True', 'true'):
    return True
  return s

def _to_str(s):
  if s is None:
    raise Exception("Cannot convert None value to config setting.")
  if not isinstance(s, str):
    return str(s)
  return s

config = load_config()
if __name__ == '__main__':
  for k,v in config.items():
    print(f"{k}={v}")

