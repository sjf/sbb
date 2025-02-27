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
  id_1 = db.insert(P_1)
  puzzle_1 = set_id(P_1, id_1)

  id_2 = db.insert(P_2)
  puzzle_2 = set_id(P_2, id_2)

  assert id_1 != id_2
  puzzles = list(db.fetch(Puzzle))
  assert puzzles == [puzzle_1, puzzle_2]
  puzzles = list(db.fetch(Puzzle, ids=[id_1, id_2]))
  assert puzzles == [puzzle_1, puzzle_2]
  puzzles = list(db.fetch(Puzzle, ids=[id_2]))
  assert puzzles == [puzzle_2]

def test_upsert_puzzle(temp_db):
  db = DB()
  id_1 = db.insert(P_1)
  puzzle_b = Puzzle(date=D1, center_letter=C1, outer_letters=['x','y','z','j','k','l'], hints='')

  id_b = db.upsert_puzzle(puzzle_b)
  puzzle_b.id = id_b

  assert id_1 == id_b
  puzzles = list(db.fetch(Puzzle, ids=[id_1]))
  assert puzzles == [puzzle_b]

def test_insert_and_fetch_clue(temp_db):
  db = DB()
  id_1 = db.insert(CL1_A)
  clue_1 = set_id(CL1_A, id_1)
  id_2 = db.insert(CL1_B)
  clue_2 = set_id(CL1_B, id_2)

  clues = list(db.fetch(Clue))
  assert clues == [clue_1, clue_2]

def test_upsert_clue(temp_db):
  db = DB()
  id_1 = db.insert(CL1_A)
  clue_b = deepcopy(CL1_A)
  id_b = db.upsert_clue(clue_b)
  clue_b.id = id_b

  assert id_1 == id_b
  clues = list(db.fetch(Clue, ids=[id_1]))
  assert clues == [clue_b]

def test_insert_definition(temp_db):
  db = DB()
  db.insert_definition(GDEF1_A)

  definitions = list(db.fetch(Definition))

  assert definitions == [Definition(word=W1_A, definitions=json.dumps(asdict(GDEF1_A)))]

def test_reinsert_definition_fails(temp_db):
  db = DB()
  db.insert_definition(GDEF1_A)
  tractor_2 = GDefinitions(word=W1_A,
    defs=[GDefinition(word=W1_A,
        retrieved_on='2024-09-09',
        raw=None,
        retrieved_from='https://something.com')])

  with pytest.raises(Exception):
    db.insert_definition(tractor_2)

def test_fetch_undefined(temp_db):
  db = DB()
  db.insert(P_1)
  db.insert(AN1_A)
  db.insert(AN1_B)
  db.insert(AN1_C)
  db.insert_definition(GDEF1_A)

  undefined = db.fetch_undefined_words()

  assert undefined == [W1_B, W1_C]


