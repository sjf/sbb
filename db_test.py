import pytest
from mbutils import *
from importer import *
from testutils import *

def test_fetch_undefined_words_none_defined(test_fake_fs):
  importer = Importer()
  importer.import_files([DB_TEST])
  db = importer.db
  undefined = db.fetch_undefined_words()
  assert undefined == ['duetted', 'toot', 'tractor']


def test_fetch_undefined_words_some_defined(test_fake_fs):
  importer = Importer()
  importer.import_files([DB_TEST])
  db = importer.db
  d = Definition(word='tractor',
    definition="A defintion of tractor",
    source='http://example.com/tractor')
  db.insert_definition(d)
  undefined = db.fetch_undefined_words()
  assert undefined == ['duetted', 'toot']

def test_fetch_undefined_words_only_new(test_fake_fs):
  importer = Importer()
  importer.import_files([DB_TEST])
  db = importer.db
  d = Definition(word='tractor',
    definition=None,
    source='http://example.com/tractor')
  db.insert_definition(d)
  undefined = db.fetch_undefined_words()
  only_new = db.fetch_undefined_words(only_new=True)

  assert undefined == ['duetted', 'toot', 'tractor']
  assert only_new == ['duetted', 'toot']

