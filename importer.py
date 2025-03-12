#!/usr/bin/env python3
import json
import emoji
import sqlite3
import unicodedata
import re
from dataclasses import dataclass, asdict, fields, field
from typing import List, Any, Dict, Optional, Set
from pyutils import *
from pyutils.settings import config
from hint_generator import HintGenerator
from wordlist import Wordlist
from es import ElasticSearch
from dicts import Dicts
from model import *
from db import *
from storage import *

DIR = 'scraped/*.json'

class Importer:
  def __init__(self):
    self.dicts = Dicts()
    self.db = DB()
    self.es = ElasticSearch()
    self.wordlist = Wordlist()

  def import_files(self, files) -> None:
    # Elastic search needs the entries to be inserted in order, so the more recent entry have precedence.
    files = sorted(files)
    files = filter(lambda f:not self.db.is_imported(f), files)
    n = 0
    for file in files:
      log(f"Importing {file}")
      content = json.loads(read(file))
      date = content['print_date']
      answers = content['answers'] + content['pangrams']
      outer_letters = content['outer_letters'].upper()
      center_letter = content['center_letter'].upper()
      missing_answers = self.missing_answers(center_letter, outer_letters, answers)

      puzzle = Puzzle(
        id = content['id'],
        date = date,
        center_letter = center_letter.upper(),
        outer_letters = outer_letters.upper(),
        missing_answers = json.dumps(missing_answers),
        hints = "") # The definitions are needed before hints can be created.
      # Re-import everything, even if rows already exist.
      # Puzzles are upate on their post day with clues later.
      puzzle_id = self.db.upsert_puzzle(puzzle, ignore_dups=True) # don't overwrite existing row.
      self.es.upsert_puzzle(date, center_letter, outer_letters)

      if content.get('clues', None): # Check if clues are present, because they are not available right away.
        for content_clue in content['clues']:
          text = get_clue_text(content_clue['text'])
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
          self.db.mark_as_imported(file) # Don't reimport this file.
      else:
        # Clues are not present in the json.
        for word in answers:
          is_pangram = word in content['pangrams']
          answer = Answer(word = word,
            puzzle_id = puzzle_id,
            clue_id = None,
            is_pangram = is_pangram)
          self.db.upsert_answer(answer)
      n += 1
    self.db.commit()
    self.es.commit()
    log(f"Imported {n} files.")

  def import_definitions(self) -> None:
    undefined = self.db.fetch_undefined_words()
    definitions = self.dicts.lookup(undefined)
    for deff in definitions:
      self.db.insert_definition(deff)
    self.db.commit()

  def generate_hints_and_missing_answers_from_defs(self) -> None:
    # Get the puzzles that havent already been analysed
    puzzles = self.db.fetch_puzzles_without_hints()
    for puzzle in puzzles:
      assert not puzzle.hints
      hg = HintGenerator(puzzle)
      hints = hg.get_puzzle_hints()
      puzzle.hints = hints
      log_debug(f'Updated {puzzle.date} with {len(hints)} hints')
    log(f"Created hints for {len(puzzles)} puzzles.")

    to_lookup = []
    for puzzle in puzzles:
      to_lookup.extend(puzzle.missing_answers)

    defs = self.db.fetch_definitions(uniq(to_lookup))
    self.wordlist.update_denylist_from_definitions(defs.values())

    c = 0
    for puzzle in puzzles:
      new_answers = self.wordlist.filter_bad(puzzle.missing_answers)
      diff = minus(puzzle.missing_answers, new_answers)
      if diff:
        c += 1
        mesg = joinl(diff, sep=", ")
        log(f'Removed {len(diff)} newly-discovered bad missing answers from {puzzle.date}: {mesg}')
      puzzle.missing_answers = new_answers
    log(f"Updated missing answers for {c} puzzles.")

    for puzzle in puzzles:
      self.db.upsert_gpuzzle(puzzle)
    self.db.commit()

  def missing_answers(self, center_letter: str, outer_letters: str, answers: List[str]) -> List[str]:
    center_letter = center_letter.lower()
    outer_letters = outer_letters.lower()
    def can_be_spelled(wordset: Set[str], words: List[str], letter_set: Set[str]) -> List[str]:
      if not center_letter in wordset:
        return []
      if wordset - letter_set == set():
        return words
      return []

    letter_set = set(list(outer_letters) + [center_letter])
    valid_words = []
    for ws,words in self.wordlist.all_words.items():
      valid_words.extend(can_be_spelled(ws, words, letter_set))
    missing_answers = minus(valid_words, answers)
    # missing_from_dict = minus(answers, valid_words)

    # print('Returned from corpus:', len(valid_words))
    # print('Answers:', len(answers))
    # print('Missing from corpus\n' + joinl(missing_from_dict))
    # print('-------')
    # print('Not in answers\n' + joinl(missing_answers))
    return missing_answers

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
  importer.generate_hints_and_missing_answers_from_defs()
  print(importer.dicts.requester.cache_status())
