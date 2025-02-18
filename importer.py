#!/usr/bin/env python3
import json
import emoji
import sqlite3
import unicodedata
import re
import requests
import requests_cache
from requests.adapters import HTTPAdapter
from dataclasses import dataclass, asdict, fields, field
from urllib3.util.retry import Retry
from typing import List, Any, Dict, Optional
from pyutils import *
from model import *
from db import *
from storage import *
from requester import *
from es import *

DIR = 'scraped/*.json'
ARCHIVE = 'archive/'
WIKTIONARY_API = 'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
MW_API = 'https://dictionaryapi.com/api/v3/references/collegiate/json/{word}?key=96fd70b1-b580-4119-b2ce-25e0988a2252'
DICT_APIS = [MW_API, WIKTIONARY_API]
REQUESTS_SQLITE_CACHE = 'scraped/requests_cache.sqlite'

class Importer:
  def __init__(self):
    self.requester = Requester(sleep=0.5)
    self.db = DB()
    self.es = ElasticSearch()

  def import_files(self, files, archive=True) -> None:
    # Elastic search needs the entries to be inserted in order, so the more recent entry have precedence.
    files = sorted(files)
    n = 0
    for file in files:
      log(f"Importing {file}")
      content = json.loads(read(file))
      date = content['print_date']
      puzzle = Puzzle(
        id = content['id'],
        date = date,
        center_letter = content['center_letter'].upper(),
        outer_letters = list(map(lambda x:x.upper(), content['outer_letters'])))
      # Re-import everything, even if rows already exist.
      # Puzzles are upate on their post day with clues later.
      puzzle_id = self.db.upsert_puzzle(puzzle)

      if content.get('clues', None): # Check if clues are present, because they are not available right away.
        for content_clue in content['clues']:
          text = content_clue['text']
          word = content_clue['word']
          is_pangram = word in content['pangrams']

          clue_id = None
          if text: # Sometimes a clue will be missing, i.e. there's no text
            url = get_clue_url(text)
            clue = Clue(text = text, url = url)
            clue_id = self.db.upsert_clue(clue)
            self.es.upsert_clue(url, word, text, date)

          answer = Answer(word = word,
            puzzle_id = puzzle_id,
            clue_id = clue_id,
            is_pangram = is_pangram)
          self.db.upsert_answer(answer)
      else:
        # Clues are not present in the json.
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
    undefined = self.db.fetch_undefined_words()
    not_found = self.import_from_dict_apis(undefined)
    if not_found:
      log_error(f"Missing definitions for {joinl(not_found, sep=', ')}")

  def import_from_dict_apis(self, words: List[str]) -> List[str]:
    if not words: return []
    n = 0
    missing = []
    log(f"Looking up {joinl(words, ', ')}")
    for word in words:
      defs = [self.retrieve_from_dict_api(word, url_fmt) for url_fmt in DICT_APIS]
      d = GDefinitions(word=word, defs=defs)
      if d.has_def:
        n += 1
      else:
        missing.append(word)
      self.db.insert_definition(d)
    self.db.conn.commit() # Commit at the end because this is very slow otherwise.
    log(f"Got definitions for {n} words, could not find {len(missing)}: {joinl(missing, sep=', ')}.")
    return missing

  def retrieve_from_dict_api(self, word: str, url_fmt: str) -> GDefinition:
    url = url_fmt.format(word=word)
    response = self.requester.get(url)
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    raw = response.json() if response else []
    result = GDefinition(word=word, retrieved_on=date, retrieved_from=url, raw=raw)
    if not response:
      return result
    if isinstance(response.json(), list) and all(isinstance(item, str) for item in response.json()):
      # MW never returns 404, it returns a list of suggested words.
      return result
    parse_dict_entry(result)
    return result

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

def get_clue_text(text: str) -> str:
  # Remove gem-stone emoji at end, this is added by one writer to indicate a hard clue.
  text = re.sub(r'([a-zA-Z].*)💎$', r'\1', text)
  return text

def to_path_safe_name(text: str, max_length: int = 100) -> str:
  """ !!! Changing this will break the existing URLs. """
  # Remove gem-stone emoji at end, this is added by one writer to indicate a hard clue.
  text = re.sub(r'([a-zA-Z].*)💎$', r'\1', text)
  # Replace emojis with the text version.
  text = emoji.demojize(text)
  # Normalize to ASCII (remove accents and non-latin characters).
  text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
  # Replace non-alphanumeric characters with hyphens.
  text = re.sub(r'[^a-zA-Z0-9\s-]', '-', text)
  # Replace spaces and multiple hyphens with a single hyphen.
  text = re.sub(r'[\s-]+', '-', text)
  # Remove leading and trailing hyphens.
  text = text.strip('-')
  # Lowercase the final text.
  text = text.lower()
  if len(text) > max_length:
    # Truncate.
    text = text[:max_length]
    # Split at hyphen.
    text = text.rsplit('-', 1)[0]
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
