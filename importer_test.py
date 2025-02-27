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

FILES = [FILE_1, FILE_2]

def test_importfiles_succeeds(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files(FILES)

  mock_es["update"].assert_has_calls(ES_UPDATES)

  clue_pages = importer.db.fetch_gclue_pages()
  assert clue_pages == GC_PAGES

  puzzles = importer.db.fetch_gpuzzles()
  for i in range(len(puzzles)):
    assert puzzles[i] == GPS[i]
  assert puzzles == GPS

  answers = importer.db.fetch_ganswers()
  assert answers == AS

def test_reimportfiles_succeeds(temp_db, fake_files, mock_es):
  importer = imp.Importer()

  importer.import_files(FILES, archive=False)
  importer.import_files(FILES)

  mock_es["update"].assert_has_calls(ES_UPDATES + ES_UPDATES)
  assert importer.db.fetch_gpuzzles() == GPS
  assert importer.db.fetch_ganswers() == AS

def test_reimportfiles_with_new_clues(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files([FILE_1_NOCLUES], archive=False)

  assert mock_es["update"].call_count == 0
  assert importer.db.fetch_ganswers() == AS_NC_1
  puzzle = deepcopy(GP_1)
  puzzle._answers = AS_NC_1
  assert importer.db.fetch_gpuzzles() == [puzzle]
  clue_pages = importer.db.fetch_gclue_pages()
  assert clue_pages == []

  # Reimport with clues.
  importer.import_files([FILE_1], archive=False)

  mock_es["update"].assert_has_calls(ES_UPDATES_1)
  assert importer.db.fetch_ganswers() == AS_1
  assert importer.db.fetch_gpuzzles() == [GP_1]

def test_import_definitions(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files([FILE_1], archive=False)
  assert importer.db.fetch_undefined_words() == sorted([W1_A, W1_B, W1_C])

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

@pytest.mark.parametrize('input_str, expected', [
  ('Moving to and fro💎', 'Moving to and fro')
])
def test_get_clue_text(input_str, expected):
  assert imp.get_clue_text(input_str) == expected

def test_to_path_safe_name_truncates():
  assert imp.to_path_safe_name('foo bar buz', 10) == 'foo-bar'
  assert imp.to_path_safe_name('foo bar buz', 11) == 'foo-bar-buz'
