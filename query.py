import sys
import logging
import os
from copy import deepcopy
import json
import langcodes
from flask import flash
from pyutils import *

import urllib
from typing import List, Any, Dict, Optional

class Query:
  def __init__(self, args=Dict[str,str]):
    self.term = _sanitize(args.get('q', ''))
    self.page_num = _get_page_num_from_request(args) or 1

  @property
  def has_search_query(self) -> bool:
    return bool(self.term)

  def __str__(self):
    dict_ = filterd(lambda k,v:not k.startswith('__'), self.__dict__)
    return f'<Query {dict_}>'

def is_set(args, key):
  if not key in args:
    return False
  # Only whitespace is not considered a value.
  value = args[key].strip()
  return bool(value)

def _sanitize(s):
  s = s.strip("'") # Dont strip double quotes.
  s = s.strip()    # Only whitespace will become the empty string.
  return s

def _get_page_num_from_request(args) -> Optional[int]:
  if not is_set(args, 'page'):
    return None
  try:
    val = int(args['page'])
  except ValueError:
    return None
  if val > config['MAX_PAGE_NUM']:
    flash("Something went wrong")
    return None
  return val
