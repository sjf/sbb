import os
import tempfile
import requester
import pytest
from typing import Generator
from unittest.mock import patch, call
from pyutils import *
from pyutils.settings import config
from testdata import HS_1
import db

@pytest.fixture
def fake_files(fs, monkeypatch) -> None:
  fs.pause()

  test_files = {}
  for file in ls("test-data/*.json"):
    dest = joinp('scraped', basename(file))
    test_files[dest] = read(file)

  test_files['words.txt'] = 'aaa'
  test_files['allowlist.txt'] = 'aaa'
  test_files['denylist.txt'] = 'aaa'
  requests_cache = read('test-data/requests_cache.sqlite', binary=True)

  fs.resume()

  for filename,content in test_files.items():
    write(filename, content, create_dirs=True)

  mkdir('data') # auto creating the dirs doesnt work in the fakefs, idk why.
  write('data/requests_cache.sqlite', requests_cache, binary=True, create_dirs=False)

@pytest.fixture
def temp_db(fs, monkeypatch) -> None:
  fs.pause()
  schema = read('schema.sql')
  fs.resume()
  write('schema.sql', schema)
  config['DB_FILE'] = 'memorydb?mode=memory&cache=shared'
  config['REQUESTS_SQLITE_CACHE'] = ':memory:'

@pytest.fixture
def mock_es(fs) -> Generator:
  write(config.get('ELASTIC_API_KEY_FILE'), 'test-elastic-api-key', create_dirs=True)

  with patch("elasticsearch.Elasticsearch.search") as mock_search, \
       patch("elasticsearch.Elasticsearch.update") as mock_update:
    mock_search.return_value = {
      "hits": {"hits": [{"_source": {"text": "Fake Clue"}}]}
    }
    mock_update.return_value = {
      "_index": config.get('INDEX'),
      "_id": "test-id-123",
      "result": "updated"
    }
    yield {"search": mock_search, "update": mock_update}

@pytest.fixture
def mock_hg() -> Generator:
  with patch("hint_generator.HintGenerator.get_puzzle_hints") as mock_get_puzzle_hints:
    mock_get_puzzle_hints.return_value = HS_1
    yield mock_get_puzzle_hints

from pprint import pformat

def assert_calls(mock, calls):
  mc = mock.mock_calls
  if mc != calls:
    i = 0
    while i < min(len(mc), len(calls)):
      assert mc[i] == calls[i], f"Position [{i}]:\nExpected\n{mc[i]}]\nGot\n{calls[i]}\nActual Calls:\n{pformat(mock.mock_calls)}"
      i += 1
    if i < len(mc):
      pytest.fail(f"Missing expected calls:\n{pformat(mc[i:])}")
    elif i < len(calls):
      pytest.fail(f"Got extra calls:\n{pformat(calls[i:])}")

    pytest.fail(f"\nExpected Calls:\n{pformat(calls)}\n\nActual Calls:\n{pformat(mock.mock_calls)}")


