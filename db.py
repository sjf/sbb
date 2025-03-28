#!/usr/bin/env python3
import json
import sqlite3
import unicodedata
import re
import dacite
import filecmp
from dataclasses import dataclass, asdict, fields, field
from typing import List, Any, Dict, Optional, Tuple
from collections import defaultdict
from pyutils import *
from storage import *
from model import *
from mw import *

SCHEMA = 'schema.sql'
MAPPING = {Puzzle: 'puzzles', Answer: 'answers', Clue: 'clues', Definition: 'definitions', Page: 'generated'}

class DB:
  def __init__(self):
    log(f"Opening SqliteDB {config['DB_FILE']}")
    self.conn = sqlite3.connect('file:' + config['DB_FILE'], uri=True)
    # Return rows as dictionaries (column name access)
    self.conn.row_factory = sqlite3.Row
    if config['DEBUG_DB']:
      self.conn.set_trace_callback(lambda x:print(x))
    self.cursor = self.conn.cursor()

    # Create tables if they don't exist
    cursor = self.conn.execute(
      "SELECT name FROM sqlite_master WHERE type='table' AND name='puzzles'")
    if cursor.fetchone() is None:
      log("Creating tables...")
      self.conn.executescript(read(SCHEMA))
      self.conn.commit()

  def __del__(self):
    try:
      self.conn.commit()
      self.conn.close()
    except Exception as e:
      print(f"Error committing DB: {e}")

  def commit(self) -> None:
    self.conn.commit()

  def insert(self, dataclass_instance, ignore_dups=False, replace_term='') -> int:
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

  def upsert_gpuzzle(self, p: GPuzzle) -> int:
    puzzle = Puzzle(
      date=p.date,
      center_letter=p.center_letter,
      outer_letters=joinl(p.outer_letters, sep=''),
      missing_answers=json.dumps(p.missing_answers),
      hints=json.dumps([ asdict(h) for h in p.hints ]))
    return self.upsert_puzzle(puzzle)

  def upsert_puzzle(self, puzzle: Puzzle, ignore_dups: bool=False) -> int:
    columns = DB.to_dict(puzzle).keys() - 'id'
    if ignore_dups:
      replace_term = ''
    else:
      updates = joinl([ f"{col} = excluded.{col}" for col in columns], sep=', ')
      replace_term = f"ON CONFLICT(date) DO UPDATE SET {updates}"

    last_id = self.insert(puzzle, ignore_dups=ignore_dups, replace_term=replace_term)
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

  def insert_definition(self, gdefs: GDefinitions) -> None:
    d = Definition(word=gdefs.word, definitions=json.dumps(asdict(gdefs)))
    self.insert(d)

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
      # print(url, mapl(lambda x:x.word, answers))
      by_word = defaultdict(list)
      for answer in answers:
        by_word[answer.word].append(answer)
      clue_answers = []

      for word,anss in by_word.items():
        # print('  ', url, word, mapl(lambda a:a.text, anss))
        puzzle_dates = sorted(mapl(lambda x:x.puzzle_date,anss), reverse=True)
        clue_answers.append(GClueAnswer(
          word=anss[0].word,
          text=anss[0].text, # I am assuming the clue text is the same if the url is the same.
          puzzle_dates=puzzle_dates,
          definitions=anss[0].definitions))
      result.append(GCluePage(url=url, _clue_answers=clue_answers))
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
      SELECT a.word, a.is_pangram, p.date as puzzle_date, c.text, c.url, d.definitions
      FROM answers a
      LEFT JOIN clues c ON a.clue_id = c.id
      JOIN puzzles p on a.puzzle_id = p.id
      LEFT JOIN definitions d on a.word = d.word;
      """)

    result = []
    for row in self.cursor.fetchall():
      data = dict(row)
      word = data['word']
      text = data['text']
      url = data['url']
      definitions = DB.deserialize_gdefs(word, data['definitions'])
      if not text:
        # Clue is not available, try to come up with one.
        clue = self.get_clue_by_word(word)
        if clue:
          text = clue.text
          url = clue.url
        else:
          text = get_clue_from_def(definitions)
          url = None # No URL for generated clues.
      answer = GAnswer(
        word = word,
        is_pangram = bool(data['is_pangram']),
        text = text,
        puzzle_date = data['puzzle_date'],
        url = url,
        definitions = definitions)
      result.append(answer)
    result = sorted(result)
    return result

  def fetch_gwords(self) -> List[GWordDefinition]:
    # Get all words and their definitions.
    self.cursor.execute("""
      SELECT distinct a.word, d.definitions
      FROM answers a
      LEFT JOIN definitions d on a.word = d.word;
      """)
    result = []
    for row in self.cursor.fetchall():
      data = dict(row)
      word = data['word']
      definitions = DB.deserialize_gdefs(word, data['definitions'])
      definition = definitions.deff if definitions.has_def else None
      answer = GWordDefinition(word=word, definition=definition)
      result.append(answer)
    result = sorted(result)
    return result

  def fetch_gpuzzles(self, limit=None, where_term="") -> List[GPuzzle]:
    # The answers group by url.
    by_date = defaultdict(list)
    for answer in self.fetch_ganswers():
      by_date[answer.puzzle_date].append(answer)

    query = """
      SELECT *
      FROM puzzles p
      {where_term}
      ORDER BY p.date DESC
      {limit_term};
    """
    limit_term = f"LIMIT {limit}" if limit else ""
    # print(query.format(limit_term=limit_term, where_term=where_term))
    self.cursor.execute(query.format(limit_term=limit_term, where_term=where_term))
    result = []
    for row in self.cursor.fetchall():
      # print(dict(row))
      answers = by_date[row['date']]
      hints = self.deserialize_hints(row['hints'])
      puzzle = GPuzzle(
          date=row['date'],
          center_letter=row['center_letter'],
          outer_letters=list(row['outer_letters']),
          _answers=answers,
          missing_answers=json.loads(row['missing_answers']),
          hints=hints)
      result.append(puzzle)
    return result

  def fetch_puzzles_without_hints(self) -> List[GPuzzle]:
    where_term = "WHERE hints IS ''"
    return self.fetch_gpuzzles(where_term=where_term)

  def fetch_definitions(self, words: List[str]) -> Dict[str, GDefinitions]:
    query = """
      SELECT *
      FROM definitions
      WHERE word IN ({placeholders});"""
    placeholders = DB.placeholders(len(words))
    self.cursor.execute(query.format(placeholders=placeholders), words)
    result = {}
    for row in self.cursor.fetchall():
      word = row['word']
      result[word] = DB.deserialize_gdefs(word, row['definitions'])
    return result

  def fetch_undefined_words(self) -> List[str]:
    query = """
      SELECT DISTINCT word
      FROM (
        SELECT a.word
        FROM answers a
        LEFT JOIN definitions d ON a.word = d.word
        WHERE d.definitions IS NULL
        UNION
        SELECT json_each.value
        FROM puzzles p, json_each(p.missing_answers)
        LEFT JOIN definitions d ON json_each.value = d.word
        WHERE d.definitions IS NULL
      ) AS combined
      ORDER BY word;"""
    return self._fetch_values(query)

  def _fetch_values(self, query: str) -> List[str]:
    """
      For use with queries that just return a single value from each row.
      Returns a list of string values returned from the query.
    """
    self.cursor.execute(query)
    rows = self.cursor.fetchall()
    result = mapl(lambda x:x[0], rows)
    return result

  def is_imported(self, name: str) -> bool:
    query = "SELECT 1 FROM imported WHERE name = ? LIMIT 1"
    self.cursor.execute(query, (name,))
    return self.cursor.fetchone() is not None

  def mark_as_imported(self, name: str) -> None:
    query = "INSERT INTO imported (name) VALUES (?) ON CONFLICT(name) DO NOTHING"
    self.cursor.execute(query, (name,))

  def is_generated(self, path: str, lastmod: Optional[str]=None) -> bool:
    and_term = f"AND lastmod >= {lastmod}" if lastmod else ''
    query = """
      SELECT 1 FROM generated
      WHERE path = ? AND needs_regen = FALSE {and_term}
      LIMIT 1"""
    self.cursor.execute(query.format(and_term=and_term), (path,))
    return self.cursor.fetchone() is not None

  def mark_as_generated(self, path: str, lastmod: str, needs_regen: bool=False) -> None:
    query = """
      INSERT INTO generated (path, lastmod, needs_regen)
      VALUES (?,?,?)
      ON CONFLICT(path) DO UPDATE
        SET lastmod = excluded.lastmod, needs_regen = excluded.needs_regen
    """
    self.cursor.execute(query, (path, lastmod, needs_regen))

  def get_pages(self) -> List[Page]:
    return self.fetch(Page)

  def clear_generated(self) -> None:
    query = f"DELETE FROM generated"
    self.cursor.execute(query)

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
  def deserialize_gdefs(word: str, gdefs_json: str) -> GDefinitions:
    if not gdefs_json:
      return GDefinitions(word=word, defs=[])
    data = json.loads(gdefs_json)
    return dacite.from_dict(data_class=GDefinitions, data=data)

  @staticmethod
  def deserialize_hints(hints_json: str) -> List[Hint]:
    if not hints_json:
      return []
    data = json.loads(hints_json)
    return [ dacite.from_dict(data_class=Hint, data=o) for o in data ]

  @staticmethod
  def columns(dataclass_instance) -> List[str]:
    return [f.name for f in fields(type(dataclass_instance))]

  @staticmethod
  def placeholders(n):
    return ','.join(['?'] * n)
