#!/usr/bin/env python3

import json
import time
import requests
import requests_cache
from requests.adapters import HTTPAdapter
from dataclasses import dataclass, asdict, fields, field
from urllib3.util.retry import Retry
from typing import List, Any, Dict, Optional
from mbutils import *

REQUESTS_SQLITE_CACHE = 'scraped/requests_cache.sqlite'

class Requester:
  """
  Makes HTTP requests using requests module.
  It has a cache (of unlimited size and no expiration).
  It uses exponential backoff for retries.
  Can sleep between requets.
  """
  def __init__(self, user_agent=None, sleep=None):
    self.user_agent = user_agent
    self.sleep = sleep

    # Set up cache for http requests.
    self.session = requests_cache.CachedSession(
      REQUESTS_SQLITE_CACHE,  # Cache stored on disk
      backend='sqlite',
      allowable_codes=(200, 404),
      expire_after=None,  # No expiration
      stale_if_error=True)  # Use stale cache if there's an error
    self.session.cache.control = 'etag'
    self.cache_hits = 0
    self.cache_misses = 0

    # Set up retry with exponential backoff
    retries = Retry(
      total=5,
      backoff_factor=2,
      status_forcelist=[429, 500, 502, 503, 504],
      respect_retry_after_header=True)
    adapter = HTTPAdapter(max_retries=retries)
    self.session.mount('https://', adapter)

  def get(self, url, headers={}) -> Optional[requests.Response]:
    if self.cache_misses > 0 and self.sleep:
      # Pause if its not the first request
      time.sleep(self.sleep)

    if self.user_agent and not 'User-Agent' in headers:
      headers['User-Agent'] = self.user_agent

    response = self.session.get(url)

    if response.from_cache:
      self.cache_hits += 1
    else:
      log(f"Getting {url}")
      self.cache_misses += 1

    if response.status_code == 404:
      return None
    response.raise_for_status()
    return response

  def get_json(self, url, headers={}):
    try:
      response = self.get(url, headers)
      if not response:
        log_error(f'Could not retrieve {url}: Got:\n{str(response)} {response.reason}')
        return None
      return json.loads(response.text)
    except json.JSONDecodeError as e:
      log_error(f'Could not decode json for {url}: {str(e)}. Got:\n{str(response)} {response.text}')
      return None

  def cache_status(self) -> str:
    total = self.cache_hits + self.cache_misses
    pc = percent(self.cache_hits, total)
    return f'Cache hit rate {pc} for {total} total requests'
