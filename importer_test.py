#!/usr/bin/env python3
import os
import pytest
import json
import db
import importer as imp
from copy import deepcopy
from mbutils import *
from testutils import *

FILES = [DB_TEST, IMPORTER_TEST]

def test_importfiles_succeeds(temp_db, fake_files):
  importer = imp.Importer()
  importer.import_files(FILES)

  clue_pages = importer.db.fetch_gclue_pages()
  assert clue_pages == GCLUE_PAGES

  puzzles = importer.db.fetch_gpuzzles()
  for i in range(len(puzzles)):
    assert puzzles[i] == GPUZZLES[i]
  assert puzzles == GPUZZLES

  latest = importer.db.fetch_latest_gpuzzle()
  assert latest == GPUZZLE_2

  answers = importer.db.fetch_ganswers()
  assert answers == ANSWERS

def test_re_importfiles_succeeds(temp_db, fake_files):
  importer = imp.Importer()
  importer.import_files(FILES, archive=False)
  importer.import_files(FILES)

  assert importer.db.fetch_gpuzzles() == GPUZZLES
  assert importer.db.fetch_ganswers() == ANSWERS

def test_re_importfiles_without_clues(temp_db, fake_files):
  importer = imp.Importer()
  importer.import_files([DB_TEST, IMPORTER_TEST_NO_CLUES], archive=False)

  # answers = importer.db.fetch_ganswers()
  # for i in range(len(ANSWERS_P2_NO_CLUE)):
  #   assert answers[i] == ANSWERS_P2_NO_CLUE[i], i
  assert importer.db.fetch_ganswers() == sorted(ANSWERS_P1 + ANSWERS_P2_NO_CLUE)
  puzzle = deepcopy(GPUZZLE_2)
  puzzle._answers = ANSWERS_P2_NO_CLUE
  assert importer.db.fetch_gpuzzles() == [puzzle, GPUZZLE_1]
  clue_pages = importer.db.fetch_gclue_pages()
  assert clue_pages == GCLUE_PAGES_P1

  # Reimport with clues.
  importer.import_files([IMPORTER_TEST], archive=False)
  assert importer.db.fetch_ganswers() == ANSWERS
  assert importer.db.fetch_gpuzzles() == GPUZZLES

def test_import_definitions(temp_db, fake_files):
  importer = imp.Importer()
  importer.import_files([DB_TEST], archive=False)
  assert importer.db.fetch_undefined_words() == ['duetted', 'toot', 'tractor']

  importer.import_definitions()

  assert importer.db.fetch_undefined_words() == []

@pytest.mark.parametrize('input_str, expected', [
  ('foo bar: buz (something)', 'foo-bar-buz-something'),
  ('FOO BAR', 'foo-bar'),
  ('Учебное пособие', ''),
  ('l\'Île Esthétisme', 'l-ile-esthetisme'),
  ('👁🦷', 'eye-tooth')
])
def test_to_path_safe_name(input_str, expected):
  assert imp.to_path_safe_name(input_str) == expected
