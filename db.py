#!/usr/bin/env python3
from mbutils import *
import json
import sqlite3
import unicodedata
import re
from dataclasses import dataclass, asdict, fields, field
from typing import List, Any, Dict, Optional
from model import *

DIR = 'scraped/*.json'
DB_FILE = 'sbb.db'
SCHEMA = 'setup.sql'

# Storage classes, generated from the schema.
@dataclass
class Puzzle:
  date: str
  center_letter: str
  outer_letters: List[str]
  answers: List[str]
  pangrams: List[str]
  id: int | None = None

@dataclass
class Clue:
  # url: str
  text: str
  id: int | None = None

@dataclass
class Answer:
  answer: str
  puzzle_id: str
  id: int | None = None

@dataclass
class PuzzleClue:
  puzzle_id: str
  clue_id: int
  id: int | None = None

@dataclass
class ClueAnswer:
  clue_id: int
  answer_id: int
  id: int | None = None

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

  def insert(self, table_name: str, dataclass_instance, ignore_dups = False) -> int:
    # print(f"Importing {dataclass_instance}")
    data = DB.to_dict(dataclass_instance)
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    replace_term = ' OR IGNORE' if ignore_dups else ""
    sql = f"INSERT{replace_term} INTO {table_name}({columns}) VALUES ({placeholders}) RETURNING id"
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

  def fetch(self, table, cls):
    self.cursor.execute(f"SELECT * FROM {table}")
    while row := self.cursor.fetchone():
      yield DB.from_dict(cls, dict(row))

  def fetch_gclues(self) -> List[GClue]:
    rows = self.fetch_clues()
    clues: Dict[int, GClue] = {}
    for row in rows:
      id_ = row['id']
      if id_ in clues:
        clue = clues[id_]
      else:
        clue = GClue(id=id_, text=row['text'])
        clues[id_] = clue
      clue.add_answer(GAnswer(answer=row['answer'], puzzle_date=row['puzzle_date']))
    result = list(clues.values())
    return result

  def fetch_clues(self) -> List[dict]:
    self.cursor.execute("""
      SELECT c.id AS id,
             c.text AS text,
             a.answer AS answer,
             p.date AS puzzle_date
      FROM clues c
      JOIN clue_answers ca ON c.id = ca.clue_id
      JOIN answers a ON a.id = ca.answer_id
      JOIN puzzles p ON a.puzzle_id = p.id
      ORDER BY c.id, p.date;""")
    rows = self.cursor.fetchall()
    result = mapl(dict, rows)
    return result

  def fetch_gpuzzles(self, only_latest=False) -> List[GPuzzle]:
    rows = self.fetch_puzzles(only_latest)
    puzzles: Dict[int, GPuzzle] = {}
    for row in rows:
      # print(row)
      id_ = row['id']
      if id_ in puzzles:
        puzzle = puzzles[id_]
      else:
        puzzle = GPuzzle(id=id_,
          date=row['date'],
          center_letter=row['center_letter'],
          outer_letters=split(row['outer_letters'],','),
          answers=split(row['answers'],','),
          pangrams=split(row['pangrams'],','))
        puzzles[id_] = puzzle
      puzzle.add_clue(GPuzzleClue(text=row['clue_text'], answer=row['clue_answer']))
    result = list(puzzles.values())
    return result

  def fetch_latest_gpuzzle(self) -> GPuzzle:
    puzzles = self.fetch_gpuzzles(only_latest=True)
    assert len(puzzles) == 1, puzzles
    return puzzles[0]


  def fetch_puzzles(self, only_latest) -> List[dict]:
    latest_term = " WHERE p.date = (SELECT MAX(date) FROM puzzles)" if only_latest else ""

    self.cursor.execute(f"""
      SELECT p.*,
             c.text AS clue_text,
             a.answer AS clue_answer
      FROM puzzles p
      JOIN answers a ON p.id = a.puzzle_id
      JOIN clue_answers ca ON a.id = ca.answer_id
      JOIN clues c ON ca.clue_id = c.id
      {latest_term}
      ORDER BY p.date, c.id;""")
    rows = self.cursor.fetchall()
    result = mapl(dict, rows)
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
    return data


