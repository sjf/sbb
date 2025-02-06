#!/usr/bin/env python3
import os
import pytest
import json
import db
import importer as imp
from copy import deepcopy
from unittest.mock import patch
from pyutils import *
from testutils import *

FILES = [DB_TEST, IMPORTER_TEST]

def test_importfiles_succeeds(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files(FILES)

  mock_es["update"].assert_has_calls(ES_UPDATES)

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

def test_reimportfiles_succeeds(temp_db, fake_files, mock_es):
  importer = imp.Importer()

  importer.import_files(FILES, archive=False)
  importer.import_files(FILES)

  mock_es["update"].assert_has_calls(ES_UPDATES + ES_UPDATES)
  assert importer.db.fetch_gpuzzles() == GPUZZLES
  assert importer.db.fetch_ganswers() == ANSWERS

def test_reimportfiles_without_clues(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files([IMPORTER_TEST_NO_CLUES], archive=False)

  assert mock_es["update"].call_count == 0
  # answers = importer.db.fetch_ganswers()
  # for i in range(len(ANSWERS_P2_NO_CLUE)):
  #   assert answers[i] == ANSWERS_P2_NO_CLUE[i], i
  assert importer.db.fetch_ganswers() == sorted(ANSWERS_P2_NO_CLUE)
  puzzle = deepcopy(GPUZZLE_2)
  puzzle._answers = ANSWERS_P2_NO_CLUE
  assert importer.db.fetch_gpuzzles() == [puzzle]
  clue_pages = importer.db.fetch_gclue_pages()
  assert clue_pages == []

  # Reimport with clues.
  importer.import_files([IMPORTER_TEST], archive=False)

  mock_es["update"].assert_has_calls(ES_UPDATES_P2)
  assert importer.db.fetch_ganswers() == ANSWERS_P2
  assert importer.db.fetch_gpuzzles() == [GPUZZLE_2]

def test_import_definitions(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files([DB_TEST], archive=False)
  assert importer.db.fetch_undefined_words() == ['duetted', 'toot', 'tractor']

  importer.import_definitions()

  assert importer.db.fetch_undefined_words() == []

@pytest.mark.parametrize('input_str, expected', [
  ('foo bar: buz (something)', 'foo-bar-buz-something'),
  ('foo bar 💎', 'foo-bar'),
  (' foo bar ', 'foo-bar'),
  ('FOO BAR', 'foo-bar'),
  ('Учебное пособие', ''),
  ('l\'Île Esthétisme', 'l-ile-esthetisme'),
  ('👁🦷', 'eye-tooth'),
  ('👁🦷💎', 'eye-tooth-gem-stone'),
])
def test_to_path_safe_name(input_str, expected):
  assert imp.to_path_safe_name(input_str) == expected

def test_to_path_safe_name_truncates():
  assert imp.to_path_safe_name('foo bar buz', 10) == 'foo-bar'
  assert imp.to_path_safe_name('foo bar buz', 11) == 'foo-bar-buz'
