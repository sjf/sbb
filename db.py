#!/usr/bin/env python3
from mbutils import *
import json
import sqlite3
import unicodedata
import re
from dataclasses import dataclass, asdict, fields, field
from typing import List, Any, Dict, Optional
from collections import defaultdict
from model import *

DIR = 'scraped/*.json'
DB_FILE = 'nyt.db'
SCHEMA = 'schema.sql'
DEBUG = os.environ.get('DEBUG', False)

# Storage classes, generated from the schema.
@dataclass
class Puzzle:
  date: str
  center_letter: str
  outer_letters: List[str]
  id: Optional[int] = None

@dataclass
class Answer:
  word: str
  is_pangram: bool
  puzzle_id: int
  clue_id: Optional[int]
  id: Optional[int] = None

@dataclass
class Clue:
  text: str
  url: str
  id: Optional[int] = None

@dataclass
class Definition:
  word: str
  definition: Optional[str]
  source: str
  retrieved_on: str

MAPPING = {Puzzle: 'puzzles', Answer: 'answers', Clue: 'clues', Definition: 'definitions'}

class DB:

  def __init__(self):
    log(f"Opening db {DB_FILE}")
    self.conn = sqlite3.connect(DB_FILE)
    # Return rows as dictionaries (column name access)
    self.conn.row_factory = sqlite3.Row
    if DEBUG:
      self.conn.set_trace_callback(lambda x:print(x))
    self.cursor = self.conn.cursor()

    # Create tables if they don't exist
    cursor = self.conn.execute(
      "SELECT name FROM sqlite_master WHERE type='table' AND name='puzzles'")
    if cursor.fetchone() is None:
      log("Creating tables...")
      self.conn.executescript(read(SCHEMA))
      self.conn.commit()

  def insert(self, dataclass_instance, ignore_dups = False, replace_term = '') -> int:
    data = DB.to_dict(dataclass_instance)
    table_name = MAPPING[type(dataclass_instance)]
    columns = ', '.join(data.keys())
    placeholders = DB.placeholders(len(data))

    if ignore_dups and replace_term:
      raise Exception("Cant have ignore and replace in same statement")
    ignore_term = 'OR IGNORE' if ignore_dups else ''
    returning_term = 'RETURNING id' if 'id' in DB.columns(dataclass_instance) else ''

    sql = f"INSERT {ignore_term} INTO {table_name}({columns}) VALUES ({placeholders}) {replace_term} {returning_term}"
    try:
      # print(sql,data.values())
      self.cursor.execute(sql, tuple(data.values()))
    except sqlite3.IntegrityError as e:
      log_error(f"Failed to import into {table_name}: {dataclass_instance}: {e}")
      raise e
    prev = self.cursor.fetchone()
    if prev is None:
      return 0
    last_id = prev[0]
    return last_id

  def upsert_puzzle(self, puzzle: Puzzle) -> int:
    columns = DB.to_dict(puzzle).keys() - 'id'
    updates = joinl([ f"{col} = excluded.{col}" for col in columns], sep=', ')
    replace_term = f"ON CONFLICT(date) DO UPDATE SET {updates}"

    last_id = self.insert(puzzle, replace_term=replace_term)
    return self._last_inserted_or_get_id(last_id, 'puzzles', {'date': puzzle.date})

  def upsert_answer(self, answer: Answer) -> int:
    columns = DB.to_dict(answer).keys() - 'id'
    updates = joinl([ f"{col} = excluded.{col}" for col in columns], sep=', ')
    replace_term = f"ON CONFLICT(word,answers.puzzle_id) DO UPDATE SET {updates}"

    last_id = self.insert(answer, replace_term=replace_term)
    return self._last_inserted_or_get_id(last_id, 'answers', {'word': answer.word, 'puzzle_id': answer.puzzle_id})

  def upsert_clue(self, clue: Clue) -> int:
    assert clue.text and clue.url, clue
    columns = DB.to_dict(clue).keys() - 'id'
    updates = joinl([ f"{col} = excluded.{col}" for col in columns], sep=', ')
    replace_term = f"ON CONFLICT(text) DO UPDATE SET {updates}"

    last_id = self.insert(clue, replace_term=replace_term)
    return self._last_inserted_or_get_id(last_id, 'clues', {'text': clue.text})

  def upsert_definition(self, d: Definition) -> None:
    columns = DB.to_dict(d).keys()
    updates = joinl([ f"{col} = excluded.{col}" for col in columns], sep=', ')
    replace_term = f"ON CONFLICT(word) DO UPDATE SET {updates}"
    self.insert(d, replace_term=replace_term)

  def _last_inserted_or_get_id(self, last_id: int, table: str, where_terms: Dict[str, int | str]) -> int:
    if last_id:
      return last_id
    query = f"SELECT id FROM {table} WHERE "
    query += joinl([ f"{col} = ?" for col in where_terms.keys()])
    values = where_terms.values()
    # print(query, values)
    self.cursor.execute(query, tuple(values))
    res = self.cursor.fetchone()
    if res:
      return res[0]
    raise Exception(f"INSERT constraint failed, but could not find row in {table} with {where_terms}")

  def fetch(self, cls, ids: List[int]=[]):
    table_name = MAPPING[cls]
    query = f"SELECT * FROM {table_name}"
    if ids:
      placeholders = DB.placeholders(len(ids))
      query += f"  WHERE id IN ({placeholders})"
    self.cursor.execute(query, ids)
    while row := self.cursor.fetchone():
      yield DB.from_dict(cls, dict(row))

  def fetch_gclue_pages(self) -> List[GCluePage]:
    # The answers grouped by url.
    by_url = defaultdict(list)
    for answer in self.fetch_ganswers():
      if answer.url:
        by_url[answer.url].append(answer)
    result = []
    for url,answers in by_url.items():
      result.append(GCluePage(url=url,_answers=answers))
    result = sorted(result, key=lambda x:x.url)
    return result

  def get_clue_by_word(self, word: str) -> Optional[Clue]:
    """ Look for a clue for `word` in the db. """
    self.cursor.execute(""" SELECT c.text, c.url
    FROM answers a
    JOIN clues c ON a.clue_id = c.id
    JOIN puzzles p on a.puzzle_id = p.id
    JOIN definitions d on a.word = d.word
    WHERE a.word = ?
    ORDER BY p.date DESC
    LIMIT 1;
    """, (word,))
    for row in self.cursor.fetchall():
      return self.from_dict(Clue, row)
    return None

  def fetch_ganswers(self) -> List[GAnswer]:
    # Get all answers and their clue.
    self.cursor.execute("""
      SELECT a.word, a.is_pangram, p.date as puzzle_date, c.text, c.url, d.definition, d.source
      FROM answers a
      LEFT JOIN clues c ON a.clue_id = c.id
      JOIN puzzles p on a.puzzle_id = p.id
      LEFT JOIN definitions d on a.word = d.word;
      """)

    result = []
    for row in self.cursor.fetchall():
      data = dict(row)
      definition = dictapis_to_def(data['definition'], data['source'])
      word = data['word']
      text = data['text']
      url = data['url']
      if not text:
        # Clue is not available, try to come up with one.
        clue = self.get_clue_by_word(word)
        if clue:
          text = clue.text
          url = clue.url
        elif definition:
          text = definition.word_types[0].meanings[0].meaning
          url = None # f'/define/{word}' # NOT AVAIL YET
      answer = GAnswer(
        word = word,
        is_pangram = bool(data['is_pangram']),
        text = text,
        puzzle_date = data['puzzle_date'],
        url = url,
        definition = definition)
      result.append(answer)
    result = sorted(result)


    return result

  def fetch_gpuzzles(self, only_latest=False) -> List[GPuzzle]:
    # The answers group by url.
    by_date = defaultdict(list)
    for answer in self.fetch_ganswers():
      by_date[answer.puzzle_date].append(answer)

    query = """
      SELECT date, center_letter, outer_letters
      FROM puzzles p
      {latest_term}
      ORDER BY p.date DESC;
    """
    latest_term = " WHERE p.date = (SELECT MAX(date) FROM puzzles)" if only_latest else ""

    self.cursor.execute(query.format(latest_term = latest_term))
    result = []
    for row in self.cursor.fetchall():
      data = dict(row)
      puzzle = GPuzzle(
          date=row['date'],
          center_letter=row['center_letter'],
          outer_letters=split(row['outer_letters']),
          _answers=by_date[row['date']])
      result.append(puzzle)
    return result

  def fetch_latest_gpuzzle(self) -> GPuzzle:
    puzzles = self.fetch_gpuzzles(only_latest=True)
    assert len(puzzles) == 1, puzzles
    return puzzles[0]

  def fetch_latest_puzzle_dates(self, n: int) -> List[str]:
    query = """
      SELECT date
      FROM puzzles
      ORDER BY date DESC
      LIMIT {n};"""
    query = query.format(n = n)
    return self._fetch_values(query)

  def fetch_undefined_words(self, only_new: bool = False) -> List[str]:
    only_new_term = " AND d.source IS NULL" if only_new else ''
    query = """
      SELECT a.word
      FROM answers a
      LEFT JOIN definitions d ON a.word = d.word
      WHERE d.definition IS NULL
      {only_new_term}
      ORDER BY a.word;"""
    return self._fetch_values(query.format(only_new_term = only_new_term))

  def _fetch_values(self, query: str) -> List[str]:
    """
      For use with queries that just return a single value from each row.
      Returns a list of string values returned from the query.
    """
    self.cursor.execute(query)
    rows = self.cursor.fetchall()
    result = mapl(lambda x:x[0], rows)
    return result

  @staticmethod
  def from_dict(cls, data: Dict):
    for f in fields(cls):
      if f.type == List[str] and isinstance(data.get(f.name), str):
        data[f.name] = data[f.name].split(',')
      if f.type == bool and isinstance(data.get(f.name), int):
        data[f.name] = bool(data[f.name])
    return cls(**data)

  @staticmethod
  def to_dict(dataclass_instance) -> Dict:
    data = asdict(dataclass_instance)
    # Remove 'None' fields (like 'id' for autoincrement)
    data = {k: v for k, v in data.items() if v is not None}
    # Convert list fields to CSV
    for key, value in data.items():
      if isinstance(value, list):
        data[key] = ','.join(value)
      elif isinstance(value, int) \
        or isinstance(value, float) \
        or isinstance(value, str) \
        or isinstance(value, bool):
        data[key] = value
      else:
        raise Exception(f"Cannot write {value} of type {type(value)} to DB.")
    return data

  @staticmethod
  def columns(dataclass_instance) -> List[str]:
    return [f.name for f in fields(type(dataclass_instance))]

  @staticmethod
  def placeholders(n):
    return ','.join(['?'] * n)
