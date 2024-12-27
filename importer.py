#!/usr/bin/env python3
from mbutils import *
import json
import sqlite3
import unicodedata
import re
from dataclasses import dataclass, asdict, fields, field
from typing import List, Any, Dict, Optional
from model import *
from db import *

DIR = 'scraped/*.json'
ARCHIVE = 'archive/'

class Importer:
  def __init__(self):
    self.db = DB()

  def import_files(self, files, archive=True) -> None:
    n = 0
    for file in files:
      content = json.loads(read(file))
      puzzle = Importer.json_to_puzzle(content)
      puzzle_id = self.db.insert('puzzles', puzzle, ignore_dups = True)
      if puzzle_id != 0: # Puzzle was not already inserted
        for content_clue in content['clues']:
          answer = Answer(answer = content_clue['word'], puzzle_id = puzzle_id)
          answer_id = self.db.insert('answers', answer)

          clue = Clue(text = content_clue['text'])
          clue_id = self.db.insert_clue(clue)

          url = get_clue_url(clue)
          url_id = self.db.insert_url(Url(url=url))

          self.db.insert('clue_answers', ClueAnswer(clue_id = clue_id, answer_id = answer_id))
          self.db.insert('puzzle_clues', PuzzleClue(puzzle_id = puzzle_id, clue_id = clue_id))
          self.db.insert('url_clues', UrlClue(url_id = url_id, clue_id = clue_id), ignore_dups = True)
        n += 1
        self.db.conn.commit()
      # archive and self.archive_file(file)
      log(f"Imported {puzzle.date} from {file}")
    log(f"Imported {n} files.")

  def archive_file(self,file):
    if not exists_dir(ARCHIVE):
      mkdir(ARCHIVE)
    mv(file, ARCHIVE)

  @staticmethod
  def json_to_puzzle(content: dict[str, Any]) -> Puzzle:
    return Puzzle(
      id = content['id'],
      date = content['print_date'],
      center_letter = content['center_letter'],
      outer_letters = list(content['outer_letters']),
      answers = content['answers'],
      pangrams = content['pangrams'])

def get_clue_url(clue: Clue) -> str:
  # return f"clue/{clue.id}"
  safe_text = to_path_safe_name(clue.text)
  url = f"clue/{safe_text}"
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
