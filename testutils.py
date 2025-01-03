import os
import tempfile
import db
import importer
from model import *
from db import *
import pytest
# import json
# import db
# import tempfile
# from mbutils import *
# from importer import *

@pytest.fixture
def fake_files(fs, monkeypatch) -> None:
  fs.pause()
  test_files = {}
  for file in ls("test-data/*.json"):
    test_files[basename(file)] = read(file)
  fs.resume()

  mkdir('scraped')
  mkdir('archive')
  for file,content in test_files.items():
    write(f"scraped/{file}", content)

@pytest.fixture
def temp_db(fs, monkeypatch) -> None:
  fs.pause()
  schema = read('schema.sql')
  fs.resume()
  write('schema.sql', schema)
  monkeypatch.setattr(db, 'DB_FILE', ':memory:')
  monkeypatch.setattr(importer, 'REQUESTS_SQLITE_CACHE', ':memory:')

DB_TEST = 'scraped/db-test.json'
IMPORTER_TEST = 'scraped/importer-test.json'
IMPORTER_TEST_NO_CLUES = 'scraped/importer-test-no-clues.json'

P1_TOOT = GAnswer(word='toot', is_pangram=False, text='Beep', url='/clue/beep', puzzle_date='2024-12-18', definition=None)
P1_TRACTOR = GAnswer(word='tractor', is_pangram=False, text='Dad preferred a John Deere ____ but grandpa loved his Ford.',
      url='/clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', puzzle_date='2024-12-18', definition=None)
P1_DUETTED = GAnswer(word='duetted', is_pangram=False, text='Play together', url='/clue/play-together', puzzle_date='2024-12-18', definition=None)

P2_TOOT_ = GAnswer(word='toot_', is_pangram=False, text='Beep', url='/clue/beep', puzzle_date='2024-12-24', definition=None)
P2_TOOTED = GAnswer(word='tooted', is_pangram=False, text='beep!!', url='/clue/beep', puzzle_date='2024-12-24', definition=None)
P2_HORN = GAnswer(word='horn', is_pangram=False, text='beep', url='/clue/beep', puzzle_date='2024-12-24', definition=None)
P2_PAGE = GAnswer(word='page', is_pangram=False, text='beep', url='/clue/beep', puzzle_date='2024-12-24', definition=None)
P2_CHAIR = GAnswer(word='chair', is_pangram=False, text='to sit', url='/clue/to-sit', puzzle_date='2024-12-24', definition=None)
P2_RECLINE = GAnswer(word='recline', is_pangram=False, text='to sit', url='/clue/to-sit', puzzle_date='2024-12-24', definition=None)
P2_OUTFOXED = GAnswer(word='outfoxed', is_pangram=True, text='Smarter than a fox', url='/clue/smarter-than-a-fox', puzzle_date='2024-12-24', definition=None)


P2_TOOT__NO_CLUE = GAnswer(word='toot_', is_pangram=False, text=None, url=None, puzzle_date='2024-12-24', definition=None)
P2_TOOTED_NO_CLUE = GAnswer(word='tooted', is_pangram=False, text=None, url=None, puzzle_date='2024-12-24', definition=None)
P2_HORN_NO_CLUE = GAnswer(word='horn', is_pangram=False, text=None, url=None, puzzle_date='2024-12-24', definition=None)
P2_PAGE_NO_CLUE = GAnswer(word='page', is_pangram=False, text=None, url=None, puzzle_date='2024-12-24', definition=None)
P2_CHAIR_NO_CLUE = GAnswer(word='chair', is_pangram=False, text=None, url=None, puzzle_date='2024-12-24', definition=None)
P2_RECLINE_NO_CLUE = GAnswer(word='recline', is_pangram=False, text=None, url=None, puzzle_date='2024-12-24', definition=None)
P2_OUTFOXED_NO_CLUE = GAnswer(word='outfoxed', is_pangram=True, text=None, url=None, puzzle_date='2024-12-24', definition=None)

ANSWERS = [P2_CHAIR, P1_DUETTED, P2_HORN, P2_OUTFOXED, P2_PAGE, P2_RECLINE, P1_TOOT, P2_TOOT_, P2_TOOTED, P1_TRACTOR]
ANSWERS_P1 = [P1_DUETTED, P1_TOOT, P1_TRACTOR]
ANSWERS_P2_NO_CLUE = [P2_CHAIR_NO_CLUE, P2_HORN_NO_CLUE, P2_OUTFOXED_NO_CLUE, P2_PAGE_NO_CLUE, P2_RECLINE_NO_CLUE, P2_TOOT__NO_CLUE, P2_TOOTED_NO_CLUE]
ANSWERS_P2 = [P2_CHAIR, P2_HORN, P2_OUTFOXED, P2_PAGE, P2_RECLINE, P2_TOOT_, P2_TOOTED]

GPUZZLE_1 = GPuzzle(
  date='2024-12-18',
  center_letter='t',
  outer_letters=['a', 'c', 'f', 'k', 'o', 'r'],
  _answers=ANSWERS_P1)
GPUZZLE_2 = GPuzzle(
  date='2024-12-24',
  center_letter='d',
  outer_letters=['t', 'e', 'f', 'o', 'u', 'x'],
  _answers=ANSWERS_P2)

GPUZZLES = [GPUZZLE_2, GPUZZLE_1]

GCLUE_PAGES = [
  GCluePage(url='/clue/beep', _answers=[P2_HORN, P2_PAGE, P1_TOOT, P2_TOOT_, P2_TOOTED]),
  GCluePage(url='/clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', _answers=[P1_TRACTOR]),
  GCluePage(url='/clue/play-together', _answers=[P1_DUETTED]),
  GCluePage(url='/clue/smarter-than-a-fox', _answers=[P2_OUTFOXED]),
  GCluePage(url='/clue/to-sit', _answers=[P2_CHAIR, P2_RECLINE])
]
GCLUE_PAGES_P1 = [
  GCluePage(url='/clue/beep', _answers=[P1_TOOT]),
  GCluePage(url='/clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', _answers=[P1_TRACTOR]),
  GCluePage(url='/clue/play-together', _answers=[P1_DUETTED]),
]

# DB Classes
CLUE_1 = Clue(text='beep', url='/clue/beep')
CLUE_2 = Clue(text='to site', url='/clue/to-sit')

PUZZLE_1 = Puzzle(date=GPUZZLE_1.date, center_letter=GPUZZLE_1.center_letter, outer_letters=GPUZZLE_1.outer_letters)
PUZZLE_2 = Puzzle(date=GPUZZLE_2.date, center_letter=GPUZZLE_2.center_letter, outer_letters=GPUZZLE_2.outer_letters)
PUZZLES = [PUZZLE_1, PUZZLE_2]

ANSWER_TOOT = Answer(word='toot', is_pangram=False, puzzle_id=1, clue_id=None)
ANSWER_DUETTED = Answer(word='duetted', is_pangram=False, puzzle_id=1, clue_id=None)
ANSWER_TRACTOR = Answer(word='tractor', is_pangram=False, puzzle_id=1, clue_id=None)

DEFINITION_TRACTOR = Definition(word='tractor',
    definition="A defintion of tractor",
    source='http://example.com/tractor',
    retrieved_on='2025-01-01')
