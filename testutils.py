import os
import tempfile
import requester
import pytest
from typing import Generator
from unittest.mock import patch, call

from pyutils.settings import config
import db
from model import *
from storage import *

@pytest.fixture
def fake_files(fs, monkeypatch) -> None:
  fs.pause()
  test_files = {}
  for file in ls("test-data/*.json"):
    test_files[basename(file)] = read(file)
  fs.resume()

  for file,content in test_files.items():
    write(f"scraped/{file}", content, create_dirs=True)

@pytest.fixture
def temp_db(fs, monkeypatch) -> None:
  fs.pause()
  schema = read('schema.sql')
  fs.resume()
  write('schema.sql', schema)
  monkeypatch.setattr(db, 'DB_FILE', ':memory:')
  monkeypatch.setattr(requester, 'REQUESTS_SQLITE_CACHE', ':memory:')

@pytest.fixture
def mock_es(fs) -> Generator:
  write(config.get('ELASTIC_API_KEY_FILE'), 'test-elastic-api-key', create_dirs=True)

  with patch("elasticsearch.Elasticsearch.search") as mock_search, \
       patch("elasticsearch.Elasticsearch.update") as mock_update:
    mock_search.return_value = {
      "hits": {"hits": [{"_source": {"Title": "Fake Book"}}]}
    }
    mock_update.return_value = {
      "_index": config.get('INDEX'),
      "_id": "test-id-123",
      "result": "updated"
    }
    yield {"search": mock_search, "update": mock_update}

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
P2_NOCLUE_NO_CLUE = GAnswer(word='noclue', is_pangram=False, text=None, url=None, puzzle_date='2024-12-24', definition=None)

C1_TOOT = GClueAnswer(word='toot', text='Beep', puzzle_dates=['2024-12-18'], definition=None)
C1_TRACTOR = GClueAnswer(word='tractor', text='Dad preferred a John Deere ____ but grandpa loved his Ford.',
      puzzle_dates=['2024-12-18'], definition=None)
C1_DUETTED = GClueAnswer(word='duetted', text='Play together', puzzle_dates=['2024-12-18'], definition=None)

C2_TOOT_ = GClueAnswer(word='toot_', text='Beep', puzzle_dates=['2024-12-24'], definition=None)
C2_TOOTED = GClueAnswer(word='tooted', text='beep!!', puzzle_dates=['2024-12-24'], definition=None)
C2_HORN = GClueAnswer(word='horn', text='beep', puzzle_dates=['2024-12-24'], definition=None)
C2_PAGE = GClueAnswer(word='page', text='beep', puzzle_dates=['2024-12-24'], definition=None)
C2_CHAIR = GClueAnswer(word='chair', text='to sit', puzzle_dates=['2024-12-24'], definition=None)
C2_RECLINE = GClueAnswer(word='recline', text='to sit', puzzle_dates=['2024-12-24'], definition=None)
C2_OUTFOXED = GClueAnswer(word='outfoxed', text='Smarter than a fox', puzzle_dates=['2024-12-24'], definition=None)

C2_TOOT__NO_CLUE = GClueAnswer(word='toot_', text=None, puzzle_dates=['2024-12-24'], definition=None)
C2_TOOTED_NO_CLUE = GClueAnswer(word='tooted', text=None, puzzle_dates=['2024-12-24'], definition=None)
C2_HORN_NO_CLUE = GClueAnswer(word='horn', text=None, puzzle_dates=['2024-12-24'], definition=None)
C2_PAGE_NO_CLUE = GClueAnswer(word='page', text=None, puzzle_dates=['2024-12-24'], definition=None)
C2_CHAIR_NO_CLUE = GClueAnswer(word='chair', text=None, puzzle_dates=['2024-12-24'], definition=None)
C2_RECLINE_NO_CLUE = GClueAnswer(word='recline', text=None, puzzle_dates=['2024-12-24'], definition=None)
C2_OUTFOXED_NO_CLUE = GClueAnswer(word='outfoxed', text=None, puzzle_dates=['2024-12-24'], definition=None)
C2_NOCLUE_NO_CLUE = GClueAnswer(word='noclue', text=None, puzzle_dates=['2024-12-24'], definition=None)

ANSWERS = sorted([P2_CHAIR, P1_DUETTED, P2_HORN, P2_OUTFOXED, P2_PAGE, P2_NOCLUE_NO_CLUE, P2_RECLINE, P1_TOOT, P2_TOOT_, P2_TOOTED, P1_TRACTOR])
ANSWERS_P1 = sorted([P1_DUETTED, P1_TOOT, P1_TRACTOR])
ANSWERS_P2_NO_CLUE = sorted([P2_CHAIR_NO_CLUE, P2_HORN_NO_CLUE, P2_OUTFOXED_NO_CLUE, P2_PAGE_NO_CLUE, P2_NOCLUE_NO_CLUE, P2_RECLINE_NO_CLUE, P2_TOOT__NO_CLUE, P2_TOOTED_NO_CLUE])
ANSWERS_P2 = sorted([P2_CHAIR, P2_HORN, P2_OUTFOXED, P2_PAGE, P2_NOCLUE_NO_CLUE, P2_RECLINE, P2_TOOT_, P2_TOOTED])

GPUZZLE_1 = GPuzzle(
  date='2024-12-18',
  center_letter='T',
  outer_letters=['A', 'C', 'F', 'K', 'O', 'R'],
  _answers=ANSWERS_P1)
GPUZZLE_2 = GPuzzle(
  date='2024-12-24',
  center_letter='D',
  outer_letters=['T', 'E', 'F', 'O', 'U', 'X'],
  _answers=ANSWERS_P2)

GPUZZLES = [GPUZZLE_2, GPUZZLE_1]

GCLUE_PAGES = [
  GCluePage(url='/clue/beep', _clue_answers=[C2_HORN, C2_PAGE, C1_TOOT, C2_TOOT_, C2_TOOTED]),
  GCluePage(url='/clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', _clue_answers=[C1_TRACTOR]),
  GCluePage(url='/clue/play-together', _clue_answers=[C1_DUETTED]),
  GCluePage(url='/clue/smarter-than-a-fox', _clue_answers=[C2_OUTFOXED]),
  GCluePage(url='/clue/to-sit', _clue_answers=[C2_CHAIR, C2_RECLINE])
]
GCLUE_PAGES_P1 = [
  GCluePage(url='/clue/beep', _clue_answers=[C1_TOOT]),
  GCluePage(url='/clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', _clue_answers=[C1_TRACTOR]),
  GCluePage(url='/clue/play-together', _clue_answers=[C1_DUETTED]),
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

ES_UPDATES_P1 = [
  call(index='sbb', id='/clue/play-together', body={'doc': {'word': 'duetted', 'text': 'Play together'}, 'doc_as_upsert': True}),
  call(index='sbb', id='/clue/beep', body={'doc': {'word': 'toot', 'text': 'Beep'}, 'doc_as_upsert': True}),
  call(index='sbb', id='/clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford',
    body={'doc': {'word': 'tractor', 'text': 'Dad preferred a John Deere ____ but grandpa loved his Ford.'}, 'doc_as_upsert': True})
]
ES_UPDATES_P2 = [
  call(index='sbb', id='/clue/smarter-than-a-fox', body={'doc': {'word': 'outfoxed', 'text': 'Smarter than a fox'}, 'doc_as_upsert': True}),
  call(index='sbb', id='/clue/beep', body={'doc': {'word': 'toot_', 'text': 'Beep'}, 'doc_as_upsert': True}),
  call(index='sbb', id='/clue/beep', body={'doc': {'word': 'tooted', 'text': 'beep!!'}, 'doc_as_upsert': True}),
  call(index='sbb', id='/clue/beep', body={'doc': {'word': 'horn', 'text': 'beep'}, 'doc_as_upsert': True}),
  call(index='sbb', id='/clue/beep', body={'doc': {'word': 'page', 'text': 'beep'}, 'doc_as_upsert': True}),
  call(index='sbb', id='/clue/to-sit', body={'doc': {'word': 'chair', 'text': 'to sit'}, 'doc_as_upsert': True}),
  call(index='sbb', id='/clue/to-sit', body={'doc': {'word': 'recline', 'text': 'to sit'}, 'doc_as_upsert': True})
]
ES_UPDATES = ES_UPDATES_P1 + ES_UPDATES_P2
