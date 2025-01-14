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
from requester import *

DIR = 'scraped/*.json'
ARCHIVE = 'archive/'
DICT_API = 'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
MW_API = 'https://dictionaryapi.com/api/v3/references/collegiate/json/{word}?key=96fd70b1-b580-4119-b2ce-25e0988a2252'
REQUESTS_SQLITE_CACHE = 'scraped/requests_cache.sqlite'

class Importer:
  def __init__(self):
    self.db = DB()
    self.requester = Requester(sleep=0.5)

  def import_files(self, files, archive=True) -> None:
    n = 0
    for file in files:
      log(f"Importing {file}")
      content = json.loads(read(file))
      puzzle = Puzzle(
        id = content['id'],
        date = content['print_date'],
        center_letter = content['center_letter'].upper(),
        outer_letters = list(map(lambda x:x.upper(), content['outer_letters'])))
      # Re-import everything, even if rows already exist.
      # Puzzles are upate on their post day with clues later.
      puzzle_id = self.db.upsert_puzzle(puzzle)

      if content.get('clues', None):
        # Clues are not available right away.
        for content_clue in content['clues']:
          text = content_clue['text']
          clue_id = None
          if text:
            # Sometimes a clue will be missing, no text
            clue = Clue(text = text, url=get_clue_url(text))
            clue_id = self.db.upsert_clue(clue)

          word = content_clue['word']
          is_pangram = word in content['pangrams']
          answer = Answer(word = word,
            puzzle_id = puzzle_id,
            clue_id = clue_id,
            is_pangram = is_pangram)
          self.db.upsert_answer(answer)
      else:
        for word in content['answers'] + content['pangrams']:
          is_pangram = word in content['pangrams']
          answer = Answer(word = word,
            puzzle_id = puzzle_id,
            clue_id = None,
            is_pangram = is_pangram)
          self.db.upsert_answer(answer)

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
    date = datetime.datetime.now().strftime('%Y-%m-%d')

    for word in words:
      response = self.requester.get(url.format(word = word))
      definition = None
      if not response:
        log(f"Didn't get definition for {word} from {url}")
        missing.append(word)
      else:
        definition = json.dumps(response.json())
        n += 1

      d = Definition(word=word, definition=definition, source=url, retrieved_on=date)
      self.db.upsert_definition(d)
      self.db.conn.commit()
      # log(f"Commited definition for {word}")
    log(f"Got definitions for {n} words, could not find {len(missing)}.")
    return missing

  def archive_file(self,file):
    if not exists_dir(ARCHIVE):
      mkdir(ARCHIVE)
    mv(file, ARCHIVE)

def get_clue_url(text: str) -> str:
  safe_text = to_path_safe_name(text)
  if not safe_text:
    raise Exception(f"Could not create url for clue text '{text}'")
  url = f"/clue/{safe_text}"
  return url

def to_path_safe_name(text: str, max_length: int = 100) -> str:
  """ !!! Changing this will break the existing URLs. """
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
  print(importer.requester.cache_status())
