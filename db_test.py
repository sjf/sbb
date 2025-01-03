import pytest
from copy import deepcopy
from mbutils import *
from testutils import *

def set_id(dataclass_instance, id_):
  result = deepcopy(dataclass_instance)
  result.id = id_
  return result

def test_insert_and_fetch_puzzle(temp_db):
  db = DB()
  id_1 = db.insert(PUZZLE_1)
  puzzle_1 = set_id(PUZZLE_1, id_1)

  id_2 = db.insert(PUZZLE_2)
  puzzle_2 = set_id(PUZZLE_2, id_2)

  assert id_1 != id_2
  puzzles = list(db.fetch(Puzzle))
  assert puzzles == [puzzle_1, puzzle_2]
  puzzles = list(db.fetch(Puzzle, ids=[id_1, id_2]))
  assert puzzles == [puzzle_1, puzzle_2]
  puzzles = list(db.fetch(Puzzle, ids=[id_2]))
  assert puzzles == [puzzle_2]

def test_upsert_puzzle(temp_db):
  db = DB()
  id_1 = db.insert(PUZZLE_1)
  puzzle_b = Puzzle(date=PUZZLE_1.date, center_letter='X', outer_letters=['x','y','z','j','k','l'])

  id_b = db.upsert_puzzle(puzzle_b)
  puzzle_b.id = id_b

  assert id_1 == id_b
  puzzles = list(db.fetch(Puzzle, ids=[id_1]))
  assert puzzles == [puzzle_b]

def test_insert_and_fetch_clue(temp_db):
  db = DB()
  id_1 = db.insert(CLUE_1)
  clue_1 = set_id(CLUE_1, id_1)
  id_2 = db.insert(CLUE_2)
  clue_2 = set_id(CLUE_2, id_2)

  clues = list(db.fetch(Clue))
  assert clues == [clue_1, clue_2]

def test_upsert_clue(temp_db):
  db = DB()
  id_1 = db.insert(CLUE_1)
  clue_b = deepcopy(CLUE_1)
  id_b = db.upsert_clue(clue_b)
  clue_b.id = id_b

  assert id_1 == id_b
  clues = list(db.fetch(Clue, ids=[id_1]))
  assert clues == [clue_b]

def test_upsert_definition(temp_db):
  db = DB()
  db.upsert_definition(DEFINITION_TRACTOR)

  definitions = list(db.fetch(Definition))
  assert definitions == [DEFINITION_TRACTOR]

  tractor_2 = Definition(word='tractor',
    definition="A second meaning of this",
    source='http://foobar.com/tractor',
    retrieved_on='2024-12-31')
  db.upsert_definition(tractor_2)

  definitions = list(db.fetch(Definition))
  assert definitions == [tractor_2]

def test_fetch_undefined_words_none_defined(temp_db):
  db = DB()
  db.insert(PUZZLE_1)
  db.insert(ANSWER_TRACTOR)
  db.insert(ANSWER_TOOT)
  db.insert(ANSWER_DUETTED)
  db.upsert_definition(DEFINITION_TRACTOR)

  undefined = db.fetch_undefined_words()

  assert undefined == ['duetted', 'toot']

def test_fetch_undefined_words_only_new(temp_db):
  db = DB()
  db.insert(PUZZLE_1)
  db.insert(ANSWER_TRACTOR)
  db.insert(ANSWER_TOOT)
  db.insert(ANSWER_DUETTED)
  # Definition that could not be found.
  d = Definition(word='tractor',
    definition=None,
    source='http://example.com/tractor',
    retrieved_on='2025-01-01')
  db.upsert_definition(d)
  undefined = db.fetch_undefined_words()
  only_new = db.fetch_undefined_words(only_new=True)

  assert undefined == ['duetted', 'toot', 'tractor']
  assert only_new == ['duetted', 'toot']

