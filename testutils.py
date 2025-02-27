import os
import tempfile
import requester
import pytest
from typing import Generator
from unittest.mock import patch, call

from pyutils.settings import config
import db
from model import *
from storage import *

@pytest.fixture
def fake_files(fs, monkeypatch) -> None:
  fs.pause()
  test_files = {}
  for file in ls("test-data/*.json"):
    test_files[basename(file)] = read(file)
  fs.resume()

  for file,content in test_files.items():
    write(f"scraped/{file}", content, create_dirs=True)

@pytest.fixture
def temp_db(fs, monkeypatch) -> None:
  fs.pause()
  schema = read('schema.sql')
  fs.resume()
  write('schema.sql', schema)
  monkeypatch.setattr(db, 'DB_FILE', ':memory:')
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
def mock_mw() -> Generator:
  with patch("mw.get_puzzle_hints") as mock_get_puzzle_hints:
    mock_get_puzzle_hints.return_value = HS_1
    yield mock_get_puzzle_hints

##### Test Data for files in test-data/ #####
FILE_1 = 'scraped/puzzle-1.json'
FILE_1_NOCLUES = 'scraped/puzzle-1-early.json'
FILE_2 = 'scraped/puzzle-2.json'

D1 = '2024-12-24'
D2 = '2024-12-29'

C1 = 'D'
C2 = 'L'
L1 = ['T', 'E', 'F', 'O', 'U', 'X']
L2 = ['B', 'G', 'I', 'M', 'O', 'R']
W1_A = 'outfoxed'
W1_B = 'detox'
W1_C = 'tofu'
U1_A = '/clue/defeated-a-woodland-creature'
U1_B = '/clue/go-cold-turkey'
U1_C = '/clue/soft-hard-or-pressed-soy-bean-curd'
T1_A = 'Defeated (a woodland creature)'
T1_B = 'Go cold turkey'
T1_C = 'Soft, hard, or pressed soy bean curd'
W2_A = 'imbroglio'
W2_B = 'igloo'
W2_C = 'olio'
U2_A = '/clue/an-embarrassing-situation'
U2_B = '/clue/dome-shaped-snow-house'
U2_C = '/clue/hodge-lodge'
T2_A = 'An embarrassing situation'
T2_B = 'Dome shaped snow house'
T2_C = 'Hodge lodge'

ES_UPDATES_1 = [
  call(index='sbb', id=U1_A, body={'doc': {'word': W1_A, 'text': T1_A, 'lastused': D1}, 'doc_as_upsert': True}),
  call(index='sbb', id=U1_B, body={'doc': {'word': W1_B, 'text': T1_B, 'lastused': D1}, 'doc_as_upsert': True}),
  call(index='sbb', id=U1_C, body={'doc': {'word': W1_C, 'text': T1_C, 'lastused': D1}, 'doc_as_upsert': True})
]
ES_UPDATES_2 = [
  call(index='sbb', id=U2_A, body={'doc': {'word': W2_A, 'text': T2_A, 'lastused': D2}, 'doc_as_upsert': True}),
  call(index='sbb', id=U2_B, body={'doc': {'word': W2_B, 'text': T2_B, 'lastused': D2}, 'doc_as_upsert': True}),
  call(index='sbb', id=U2_C, body={'doc': {'word': W2_C, 'text': T2_C, 'lastused': D2}, 'doc_as_upsert': True})
]
ES_UPDATES = ES_UPDATES_1 + ES_UPDATES_2

C1_A = GClueAnswer(word=W1_A, text=T1_A, puzzle_dates=[D1], definitions=GDefinitions(word=W1_A,defs=[]))
C1_B = GClueAnswer(word=W1_B, text=T1_B, puzzle_dates=[D1], definitions=GDefinitions(word=W1_B,defs=[]))
C1_C = GClueAnswer(word=W1_C, text=T1_C, puzzle_dates=[D1], definitions=GDefinitions(word=W1_C,defs=[]))
CS_1 = [C1_A, C1_B, C1_C]

C2_A = GClueAnswer(word=W2_A, text=T2_A, puzzle_dates=[D2], definitions=GDefinitions(word=W2_A,defs=[]))
C2_B = GClueAnswer(word=W2_B, text=T2_B, puzzle_dates=[D2], definitions=GDefinitions(word=W2_B,defs=[]))
C2_C = GClueAnswer(word=W2_C, text=T2_C, puzzle_dates=[D2], definitions=GDefinitions(word=W2_C,defs=[]))
CS_2 = [C2_A, C2_B, C2_C]

GC_PAGES_1 = [
  GCluePage(url=U1_A, _clue_answers=[C1_A]),
  GCluePage(url=U1_B, _clue_answers=[C1_B]),
  GCluePage(url=U1_C, _clue_answers=[C1_C]),
]
GC_PAGES_2 = [
  GCluePage(url=U2_A, _clue_answers=[C2_A]),
  GCluePage(url=U2_B, _clue_answers=[C2_B]),
  GCluePage(url=U2_C, _clue_answers=[C2_C]),
]
GC_PAGES = sorted(GC_PAGES_1 + GC_PAGES_2)

A1_A = GAnswer(word=W1_A, is_pangram=True,  text=T1_A, url=U1_A, puzzle_date=D1, definitions=GDefinitions(word=W1_A,defs=[]))
A1_B = GAnswer(word=W1_B, is_pangram=False, text=T1_B, url=U1_B, puzzle_date=D1, definitions=GDefinitions(word=W1_B,defs=[]))
A1_C = GAnswer(word=W1_C, is_pangram=False, text=T1_C, url=U1_C, puzzle_date=D1, definitions=GDefinitions(word=W1_C,defs=[]))
AS_1 = sorted([A1_A, A1_B, A1_C])

A1_NC_A = GAnswer(word=W1_A, is_pangram=True,  text=None, url=None, puzzle_date=D1, definitions=GDefinitions(word=W1_A,defs=[]))
A1_NC_B = GAnswer(word=W1_B, is_pangram=False, text=None, url=None, puzzle_date=D1, definitions=GDefinitions(word=W1_B,defs=[]))
A1_NC_C = GAnswer(word=W1_C, is_pangram=False, text=None, url=None, puzzle_date=D1, definitions=GDefinitions(word=W1_C,defs=[]))
AS_NC_1 = sorted([A1_NC_A, A1_NC_B, A1_NC_C])

A2_A = GAnswer(word=W2_A, is_pangram=True,  text=T2_A, url=U2_A, puzzle_date=D2, definitions=GDefinitions(word=W2_A,defs=[]))
A2_B = GAnswer(word=W2_B, is_pangram=False, text=T2_B, url=U2_B, puzzle_date=D2, definitions=GDefinitions(word=W2_B,defs=[]))
A2_C = GAnswer(word=W2_C, is_pangram=False, text=T2_C, url=U2_C, puzzle_date=D2, definitions=GDefinitions(word=W2_C,defs=[]))
AS_2 = sorted([A2_A, A2_B, A2_C])
AS = sorted(AS_1 + AS_2)

GP_1 = GPuzzle(date=D1, center_letter=C1, outer_letters=L1, _answers=AS_1, hints=[])
GP_2 = GPuzzle(date=D2, center_letter=C2, outer_letters=L2, _answers=AS_2, hints=[])
GPS = [GP_2, GP_1]

GDEF1_A = GDefinitions(word=W1_A,
  defs=[GDefinition(word=W1_A,
      retrieved_on='2024-01-01',
      retrieved_from='https://dictionaryapi.com/api/v3/references/collegiate/json/outfoxed?key=ABC-123',
      raw={"source-def":"outfoxed-def"},
      source_url='https://merrian-webster.com/dict/outfoxed',
      word_types=[GWordTypeDefinition(word_type='noun', meanings=[])])
  ])

H1_A = Hint(score=10, text='These words have x in the middle.', words=[W1_A, W1_B])
H1_B = Hint(score=9,  text='This word is from Japanese.',       words=[W1_C])
HS_1 = [H1_A, H1_B]

## Storage classes
P_1 = Puzzle(date=D1, center_letter=C1, outer_letters=L1, hints='')
P_2 = Puzzle(date=D2, center_letter=C2, outer_letters=L2, hints='')

CL1_A = Clue(text=T1_A, url=U1_A)
CL1_B = Clue(text=T1_B, url=U1_B)

AN1_A = Answer(word=W1_A, is_pangram=True, puzzle_id=1, clue_id=None)
AN1_B = Answer(word=W1_B, is_pangram=True, puzzle_id=1, clue_id=None)
AN1_C = Answer(word=W1_C, is_pangram=True, puzzle_id=1, clue_id=None)



