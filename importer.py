#!/usr/bin/env python3
from mbutils import *
import json
import sqlite3
import unicodedata
import re
import requests
import requests_cache
from requests.adapters import HTTPAdapter
from dataclasses import dataclass, asdict, fields, field
from urllib3.util.retry import Retry
from typing import List, Any, Dict, Optional
from model import *
from db import *

DIR = 'scraped/*.json'
ARCHIVE = 'archive/'
DICT_API = 'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
MW_API = 'https://dictionaryapi.com/api/v3/references/collegiate/json/{word}?key=96fd70b1-b580-4119-b2ce-25e0988a2252'

class Importer:
  def __init__(self):
    self.db = DB()
    self.setup_requests()

  def import_files(self, files, archive=True) -> None:
    n = 0
    for file in files:
      log(f"Importing {file}")
      content = json.loads(read(file))
      puzzle = Puzzle(
        id = content['id'],
        date = content['print_date'],
        center_letter = content['center_letter'],
        outer_letters = list(content['outer_letters']))
      puzzle_id = self.db.insert('puzzles', puzzle, ignore_dups = True)

      if puzzle_id == 0: # Puzzle was not already inserted
        log(f"Skipping {puzzle.date} from {file}, already imported")
        continue

      for content_clue in content['clues']:
        text = content_clue['text']
        clue = Clue(text = text, url=get_clue_url(text))
        clue_id = self.db.insert_clue(clue)

        word = content_clue['word']
        is_pangram = word in content['pangrams']
        answer = Answer(word = word,
          puzzle_id = puzzle_id,
          clue_id = clue_id,
          is_pangram = is_pangram)
        self.db.insert('answers', answer)

      self.db.conn.commit()
      n += 1
      log(f"Imported {puzzle.date} from {file}")
    log(f"Imported {n} files.")

  def import_definitions(self) -> None:
    words = self.db.fetch_undefined_words(only_new=True)
    words = self.import_from_api(DICT_API, words)
    words = self.db.fetch_undefined_words()
    missing = self.import_from_api(MW_API, words)
    if missing:
      log_error(f"Missing definitions for {joinl(missing)}")

  def import_from_api(self, url: str, words: List[str]) -> List[str]:
    if not words:
      return []
    n = 0
    missing = []
    log(f"Looking up {joinl(words, ', ')} in {url}")
    for word in words:
      response = self.get(url.format(word = word))
      if not response:
        log(f"Missing {word}")
        d = Definition(word=word, definition=None, source=url)
        missing.append(word)
      else:
        content = response.json()
        d = Definition(word=word, definition=json.dumps(content), source=url)
        n += 1
      self.db.insert_definition(d)
      self.db.conn.commit()
      # log(f"Commited definition for {word}")
    log(f"Got definitions for {n} words, could not find {len(missing)}.")
    return missing

  def setup_requests(self):
    # Set up cache for api requests.
    if os.getenv('PYTEST'):
      # Cant use sqlite with a backing file in unit tests.
      self.session = requests_cache.CachedSession(backend='memory', expire_after=0)
    else:
      self.session = requests_cache.CachedSession(
        '.requests_cache.sqlite',  # Cache stored on disk
        backend='sqlite',
        expire_after=None,  # No expiration
        stale_if_error=True)  # Use stale cache if there's an error
    self.session.cache.control = 'etag'
    # Set up retry with exponential backoff
    retries = Retry(
      total=5,
      backoff_factor=2,
      status_forcelist=[429, 500, 502, 503, 504],
      respect_retry_after_header=True)
    adapter = HTTPAdapter(max_retries=retries)
    self.session.mount('https://', adapter)


  def get(self, url):
    log(f"Getting {url}")
    response = self.session.get(url)
    if response.status_code == 404:
      return None
    response.raise_for_status()
    return response

  def archive_file(self,file):
    if not exists_dir(ARCHIVE):
      mkdir(ARCHIVE)
    mv(file, ARCHIVE)

def get_clue_url(text: str) -> str:
  # return f"clue/{clue.id}"
  safe_text = to_path_safe_name(text)
  url = f"/clue/{safe_text}"
  return url

def to_path_safe_name(text: str, max_length: int = 100) -> str:
  # Normalize to ASCII (remove accents)
  text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
  # Replace non-alphanumeric characters with hyphens
  text = re.sub(r'[^a-zA-Z0-9\s-]', '-', text)
  # Replace spaces and multiple hyphens with a single hyphen
  text = re.sub(r'[\s-]+', '-', text).strip('-')
  # Lowercase the final string
  text = text.lower()
  if len(text) > max_length:
    text = text[:max_length].rsplit('-', 1)[0] # Split at hyphen.
  return text

if __name__ == '__main__':
  importer = Importer()
  if len(sys.argv) > 1:
    files = sys.argv[1:]
  else:
    files = ls(DIR)
  if not files:
    log('Nothing import, exiting.')
    sys.exit(0)
  importer.import_files(files)
  importer.import_definitions()
