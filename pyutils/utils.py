import os
import subprocess
import sys
import time, datetime
import humanfriendly
import logging
import configparser
import traceback
import re
import ast
import csv
import urllib.parse
import pprint
import tldextract
import hashlib
from typing import List, Any, Dict, Optional, Tuple, TypeVar,TypeAlias
from collections.abc import Iterable
from collections import Counter, defaultdict
from .log import *
from .shell import read, stderr

### String utils ###

def md5(f: str) -> str:
  data = read(f)
  return md5_value(data)

def md5_value(s: str) -> str:
  e = s.encode('utf-8')
  return hashlib.md5(e).hexdigest()

def normalize(s, lower=True, rm_whitespace=False, rm_punctuation=True):
  """ With the default args: lowercases, collapses whitespace and strips; and removes punctuation (not letter, digit or whitespace). """
  if lower:
    s = s.lower() # lowercase

  if rm_whitespace:
    s = re.sub(r'\s', '', s) # remove all whitespace
  else:
    s = re.sub(r'\s+', ' ', s, flags=re.MULTILINE) # collapse whitespace, including newlines

  if rm_punctuation:
    s = re.sub(r'[^\w\s]', '', s) # remove chars that are not letters, digits or whitespace.

  s = s.strip() # remove leading and trailing whitespace
  return s

def split(s, sep=','):
  parts = s.split(sep)
  parts = map(lambda x:x.strip(), parts)
  parts = non_empty(parts)
  return parts

def trunc(s, max_=60):
  if len(s) > max_:
    return s[:max_-3] + '...'
  return s

def percent(n,d):
  if n == d == 0:
    return '0%'
  pc = int((n / d) * 100)
  return f'{pc}%'

def smquote(s: str, single=False) -> str:
  """ Smart quote. """
  if single:
    return f"‘{s}’"
  return f"“{s}”"

### List utils ###

def uniq(l: List[Any]):
  """ Remove duplicates while preserving order. """
  return list(dict.fromkeys(l))

def joinl(l, sep="\n", to_str=str, empty=''):
  if not l:
    return empty
  return sep.join(map(to_str,l))

def mapl(f,seq):
  return list(map(f,seq))

def filterl(f,seq):
  return list(filter(f,seq))

def containsl(list1, list2):
  return set(list2).issubset(list1)

def non_empty(l):
  return list(filter(lambda x:x, l))

def index_or_default(n, l, default):
  if len(l) <= n:
    return default
  return l[n]

def slist(o):
  return sorted(list(o))

def minus(l1, l2):
  return slist(set(l1) - set(l2))

### Dict utils ####

def dictl(d, sort_key=None, sep='\n', empty='{}', to_str_key=lambda x:x, item_sep='='):
  items = sorted(d.items(), key=sort_key)
  return joinl([f"{to_str_key(k)}{item_sep}{repr(v)}" for k,v in items], sep=sep, empty=empty)

def printd(d):
  return pprint.pprint(d)

def filterd(f, d):
  result = {}
  for k,v in d.items():
    if f(k,v):
      result[k] = v
  return result

def contains_keys(d, keys):
  return containsl(d.keys(), keys)

#### File utils ####

def file_line_reader(file_path):
  """ Generator to read file line by line, returns the line number and stripped line."""
  # DEBUG and log(f"Opening {file_path}")
  with open(file_path) as fh:
    line_num = 0
    while line := fh.readline():
      yield line.rstrip(), line_num
      line_num += 1

def read_csv(f, delimiter=',', quotechar='"'):
  result = []
  with open(f) as fh:
    reader = csv.reader(fh, delimiter=delimiter, quotechar=quotechar)
    for line in reader:
      result.append(line)
  return result

#### URL/URI utils ####

def url_params(url, keep_blank_values=True, query_only=False):
  """ Returns the URL params as dict where the value is list all the param values. """
  if query_only:
    query = url
  else:
    query = urllib.parse.urlparse(url).query # split query from url
  params = urllib.parse.parse_qs(query, keep_blank_values=keep_blank_values)
  return dict(params)

def url_wo_host(url):
  """ Returns the URL without the hostname and protocol. """
  parsed_url = urllib.parse.urlparse(url)
  new_url = ('', '', parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment)
  return urllib.parse.urlunparse(new_url)

def url_domain(url: str) -> str:
  extracted = tldextract.extract(url)
  return extracted.registered_domain

def url_path(url):
  """ Returns the URL path (without the parameters). """
  parsed_url = urllib.parse.urlparse(url)
  return parsed_url.path

def replace_url_param(url, name, value):
  params = url_params(url)
  params[name] = [value]
  query = urllib.parse.urlencode(params, doseq=True)

  parsed_url = urllib.parse.urlparse(url)
  parsed_url = parsed_url._replace(query=query)
  new_url = urllib.parse.urlunparse(parsed_url)
  return new_url

def remove_url_param(url, param):
  parsed_url = urllib.parse.urlparse(url)

  query_params = urllib.parse.parse_qs(parsed_url.query)
  query_params.pop(param, None) # Remove the specified parameter
  new_query = urllib.parse.urlencode(query_params, doseq=True)

  return urllib.parse.urlunparse(parsed_url._replace(query=new_query))

def url_decode(s):
  return urllib.parse.unquote(s)

def url_encode(s):
  return urllib.parse.quote(s)

def url_to_filename(url):
  url = url.replace('://','_')
  # Replace forbidden characters with underscores
  return re.sub(r'[<>:"/\\|?*]', '_', url)

def get_db_uri():
  DB_URI = "mysql://{user}:{password}@{host}/{db}"
  db_host = os.environ.get('DB_HOST')
  db = os.environ.get('MYSQL_DB')
  user = os.environ.get('DB_USER')
  password = read(os.environ.get('DB_PASSWORD_FILE'))
  return DB_URI.format(user=user, password=password, db=db, host=db_host)

#### Others ####

def cmp(a,b):
  # ascending
  res = (a > b) - (a < b)
  # descending
  return -res

def time_ms():
  return int(time.time() * 1000)

def printl(o, sort_key=None):
  if isinstance(o, dict):
    s = dictl(o, sort_key=sort_key)
  elif isinstance(o, Iterable):
    s = joinl(o)
  else:
    s = o
  print(s)

