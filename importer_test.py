#!/usr/bin/env python3
import os
import pytest
import json
import db
import importer as imp
from copy import deepcopy
from pyutils import *
from testutils import *
from testdata import *

FILES = [FILE_1, FILE_2]

def test_importfiles_succeeds(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files(FILES)

  assert_calls(mock_es["update"], ES_UPDATES)

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

  importer.import_files(FILES)
  importer.import_files(FILES)

  mock_es["update"].assert_has_calls(ES_UPDATES)
  assert importer.db.fetch_gpuzzles() == GPS
  assert importer.db.fetch_ganswers() == AS

def test_reimportfiles_with_new_clues(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files([FILE_1_NOCLUES])

  assert_calls(mock_es["update"], ES_UPDATES_1[0:1]) # Only puzzle is imported
  assert importer.db.fetch_ganswers() == AS_NC_1
  puzzle = deepcopy(GP_1)
  puzzle._answers = AS_NC_1
  assert importer.db.fetch_gpuzzles() == [puzzle]
  clue_pages = importer.db.fetch_gclue_pages()
  assert clue_pages == []

  # Reimport with clues.
  importer.import_files([FILE_1])

  mock_es["update"].assert_has_calls(ES_UPDATES_1)
  assert importer.db.fetch_ganswers() == AS_1
  assert importer.db.fetch_gpuzzles() == [GP_1]

def test_files_not_reimported(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files([FILE_1_NOCLUES, FILE_2])

  mock_es["update"].assert_has_calls(ES_UPDATES_2)
  assert not importer.db.is_imported(FILE_1_NOCLUES)
  assert importer.db.is_imported(FILE_2)

  importer.import_files([FILE_1_NOCLUES, FILE_2])

  mock_es["update"].assert_has_calls(ES_UPDATES_2)
  assert not importer.db.is_imported(FILE_1_NOCLUES)
  assert importer.db.is_imported(FILE_2)

def test_import_definitions(temp_db, fake_files, mock_es):
  importer = imp.Importer()
  importer.import_files([FILE_1])
  assert importer.db.fetch_undefined_words() == sorted([W1_A, W1_B, W1_C])

  importer.import_definitions()

  assert importer.db.fetch_undefined_words() == []

def test_generate_hints(temp_db, fake_files, mock_es, mock_hg):
  importer = imp.Importer()
  importer.import_files([FILE_1])
  importer.generate_hints()

  assert mock_hg.call_count == 1

  puzzle = importer.db.fetch_gpuzzles()[0]
  assert puzzle.hints == HS_1

def test_reimport_no_regen_hints(temp_db, fake_files, mock_es, mock_hg):
  importer = imp.Importer()
  importer.import_files([FILE_1_NOCLUES])
  importer.generate_hints()

  assert mock_hg.call_count == 1
  assert importer.db.fetch_gpuzzles()[0].hints == HS_1

  importer.import_files([FILE_1])
  importer.generate_hints()
  assert mock_hg.call_count == 1

  importer.import_files([FILE_1])
  importer.generate_hints()
  assert mock_hg.call_count == 1
  assert importer.db.fetch_gpuzzles()[0].hints == HS_1

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
