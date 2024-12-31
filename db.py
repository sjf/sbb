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
SCHEMA = 'setup.sql'

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
  clue_id: int
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

class DB:
  def __init__(self):
    log(f"Opening db {DB_FILE}")
    self.conn = sqlite3.connect(DB_FILE)
    # Return rows as dictionaries (column name access)
    self.conn.row_factory = sqlite3.Row
    self.cursor = self.conn.cursor()

    # Create tables if they don't exist
    cursor = self.conn.execute(
      "SELECT name FROM sqlite_master WHERE type='table' AND name='puzzles'")
    if cursor.fetchone() is None:
      log("Creating tables...")
      self.conn.executescript(read(SCHEMA))
      self.conn.commit()

  def insert(self, table_name: str, dataclass_instance, ignore_dups = False, replace_dups = False) -> int:
    # print(f"Importing {dataclass_instance}")
    data = DB.to_dict(dataclass_instance)
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])

    if ignore_dups and replace_dups:
      raise Exception("Cannot enable both ignore_dups and replace_dups")
    replace_term = ''
    if ignore_dups:
      replace_term = 'OR IGNORE'
    elif replace_dups:
      replace_term = 'OR REPLACE'

    sql = f"INSERT {replace_term} INTO {table_name}({columns}) VALUES ({placeholders}) RETURNING id"
    try:
      self.cursor.execute(sql, tuple(data.values()))
    except sqlite3.IntegrityError as e:
      log_error(f"Failed to import into {table_name}: {dataclass_instance}")
      raise e
    prev = self.cursor.fetchone()
    last_id = prev[0] if prev is not None else 0
    # print(sql, data.values(), 'id:',last_id)
    return last_id

  def insert_clue(self, clue: Clue) -> int:
    last_id = self.insert('clues', clue, ignore_dups = True)
    if last_id != 0:
      return last_id
    self.cursor.execute(f"SELECT id FROM clues WHERE text = ?", (clue.text,))
    return self.cursor.fetchone()[0]

  def insert_definition(self, d: Definition) -> None:
    query = """
    INSERT INTO definitions (word, definition, source)
    VALUES (?,?,?)
    ON CONFLICT(word)
    DO UPDATE SET
      definition = excluded.definition,
      source = excluded.source;"""
    self.cursor.execute(query, (d.word, d.definition, d.source))
    self.conn.commit()

  def fetch(self, table, cls):
    self.cursor.execute(f"SELECT * FROM {table}")
    while row := self.cursor.fetchone():
      yield DB.from_dict(cls, dict(row))

  def fetch_gclue_pages(self) -> List[GCluePage]:
    # The answers grouped by url.
    by_url = defaultdict(list)
    for answer in self.fetch_ganswers():
      by_url[answer.url].append(answer)
    result = []
    for url,answers in by_url.items():
      result.append(GCluePage(url=url,_answers=answers))
    result = sorted(result, key=lambda x:x.url)
    return result

  def fetch_ganswers(self) -> List[GAnswer]:
    # Get all answers and their clue.
    self.cursor.execute("""
      SELECT a.word, is_pangram, date as puzzle_date, text, url, definition, source
      FROM answers a
      JOIN clues c ON a.clue_id = c.id
      JOIN puzzles p on a.puzzle_id = p.id
      LEFT JOIN definitions d on a.word = d.word
      ;
      """)

    result = []
    for row in self.cursor.fetchall():
      data = dict(row)
      definition = dictapis_to_def(data['definition'], data['source'])
      answer = GAnswer(word = data['word'],
        is_pangram = data['is_pangram'],
        text = data['text'],
        puzzle_date = data['puzzle_date'],
        url = data['url'],
        definition = definition)
      result.append(answer)
    return result

  # def fetch_gclues(self, ids=[]) -> List[GClue]:
  #   rows = self.fetch_clues(ids)
  #   clues: Dict[int, GClue] = {}
  #   for row in rows:
  #     id_ = row['id']
  #     if id_ in clues:
  #       clue = clues[id_]
  #     else:
  #       clue = GClue(id=id_, text=row['text'])
  #       clues[id_] = clue
  #     def_ = dictapis_to_def(row['definition'],row['source'])
  #     clue.add_answer(GAnswer(answer=row['answer'], puzzle_date=row['puzzle_date'], definition=def_))
  #   result = list(clues.values())
  #   return result

  # def fetch_clues(self, ids: list[int]) -> List[dict]:
  #   query = """
  #     SELECT c.id AS id,
  #            c.text AS text,
  #            a.answer AS answer,
  #            d.definition as definition,
  #            d.source as source,
  #            p.date AS puzzle_date
  #     FROM clues c
  #     JOIN clue_answers ca ON c.id = ca.clue_id
  #     JOIN answers a ON a.id = ca.answer_id
  #     LEFT JOIN definitions d ON a.answer = d.word
  #     JOIN puzzles p ON a.puzzle_id = p.id
  #     {where_term}
  #     ORDER BY c.id, p.date;"""
  #   where_term = ''
  #   if ids:
  #     where_term = f" WHERE c.id IN ({','.join(map(str,ids))}) "
  #   self.cursor.execute(query.format(where_term=where_term))
  #   rows = self.cursor.fetchall()
  #   result = mapl(dict, rows)
  #   return result

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
    return self.fetch_values(query)

  def fetch_undefined_words(self, only_new: bool = False) -> List[str]:
    only_new_term = " AND d.source IS NULL" if only_new else ''
    query = """
      SELECT a.word
      FROM answers a
      LEFT JOIN definitions d ON a.word = d.word
      WHERE d.definition IS NULL
      {only_new_term}
      ORDER BY a.word;"""
    return self.fetch_values(query.format(only_new_term = only_new_term))

  def fetch_values(self, query: str) -> List[str]:
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
