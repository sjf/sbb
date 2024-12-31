#!/usr/bin/env python3
import os
import pytest
import json
import db

from mbutils import *
from importer import *
from testutils import *

FILES = [DB_TEST, IMPORTER_TEST]

def test_import_succeeds(test_fake_fs):
  importer = Importer()
  importer.import_files(FILES)

  clue_pages = importer.db.fetch_gclue_pages()
  assert clue_pages == GCLUE_PAGES

  # puzzles = importer.db.fetch_gpuzzles()
  # assert puzzles == [GPUZZLE_1, GPUZZLE_2]
  # latest = importer.db.fetch_latest_gpuzzle()
  # assert latest == GPUZZLE_2
  # clues = importer.db.fetch_gclues()
  # assert clues == GCLUES
  # assert not exists(FILE_1)
  # assert not exists(FILE_2)
  # assert exists("archive/" + basename(FILE_1))
  # assert exists("archive/" + basename(FILE_2))

def test_re_import_succeeds(test_fake_fs):
  importer = Importer()
  importer.import_files(FILES, archive=False)
  importer.import_files(FILES)

  # assert importer.db.fetch_gpuzzles() == [GPUZZLE_1, GPUZZLE_2]
  # assert importer.db.fetch_gclues() == GCLUES


