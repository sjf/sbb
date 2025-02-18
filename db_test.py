import pytest
from copy import deepcopy
from pyutils import *
from testutils import *
from db import *

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

def test_insert_definition(temp_db):
  db = DB()
  db.insert_definition(GDEFINITIONS_TRACTOR)

  definitions = list(db.fetch(Definition))

  assert definitions == [Definition(word='tractor', definitions=json.dumps(asdict(GDEFINITIONS_TRACTOR)))]

def test_reinsert_definition_fails(temp_db):
  db = DB()
  db.insert_definition(GDEFINITIONS_TRACTOR)
  tractor_2 = GDefinitions(word='tractor',
    defs=[GDefinition(word='tractor',
        retrieved_on='2024-01-01',
        raw=None,
        retrieved_from='https://something.com')])

  with pytest.raises(Exception):
    db.insert_definition(tractor_2)

def test_fetch_undefined(temp_db):
  db = DB()
  db.insert(PUZZLE_1)
  db.insert(ANSWER_TRACTOR)
  db.insert(ANSWER_TOOT)
  db.insert(ANSWER_DUETTED)
  db.insert_definition(GDEFINITIONS_TRACTOR)

  undefined = db.fetch_undefined_words()

  assert undefined == ['duetted', 'toot']


