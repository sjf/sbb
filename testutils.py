import os
import tempfile
import db
from model import *
import pytest
# import json
# import db
# import tempfile
# from mbutils import *
# from importer import *

@pytest.fixture
def test_fake_fs(fs, monkeypatch):
  fs.pause()
  schema = read('setup.sql')
  fd, temp_db = tempfile.mkstemp() # sqlite cannot use pyfakefs
  os.close(fd)
  test_files = {}
  for file in ls("test-data/*.json"):
    test_files[basename(file)] = read(file)
  fs.resume()

  monkeypatch.setattr(db, 'DB_FILE', temp_db)

  write('setup.sql', schema)
  mkdir('scraped')
  mkdir('archive')
  for file,content in test_files.items():
    write(f"scraped/{file}", content)
  yield temp_db

  # Tear down
  fs.pause()
  rm(temp_db)
  fs.resume()

# FILE_1 = 'scraped/importer-test-1.json'
DB_TEST = 'scraped/db-test.json'
IMPORTER_TEST = 'scraped/importer-test.json'

P1_TOOT = GAnswer(word='toot', is_pangram=False, text='Beep', url='/clue/beep', puzzle_date='2024-12-18', definition=None)
P1_TRACTOR = GAnswer(word='tractor', is_pangram=False, text='Dad preferred a John Deere ____ but grandpa loved his Ford.',
      url='/clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', puzzle_date='2024-12-18', definition=None)
P1_DUETTED = GAnswer(word='duetted', is_pangram=False, text='Play together', url='/clue/play-together', puzzle_date='2024-12-18', definition=None)

P2_TOOT_ = GAnswer(word='toot_', is_pangram=False, text='Beep', url='/clue/beep', puzzle_date='2024-12-24', definition=None)
P2_TOOTED = GAnswer(word='tooted', is_pangram=False, text='beep!!', url='/clue/beep', puzzle_date='2024-12-24', definition=None)
P2_HORN = GAnswer(word='horn', is_pangram=False, text='beep', url='/clue/beep', puzzle_date='2024-12-24', definition=None)
P2_PAGE = GAnswer(word='page', is_pangram=False, text='beep', url='/clue/beep', puzzle_date='2024-12-24', definition=None)
P2_CHAIR = GAnswer(word='chair', is_pangram=False, text='to sit', url='/clue/to-sit', puzzle_date='2024-12-24', definition=None)
P2_RECLINE = GAnswer(word='recline', is_pangram=False, text='to sit', url='/clue/to-sit', puzzle_date='2024-12-24', definition=None)

GPUZZLE_1 = GPuzzle(
  date='2024-12-18',
  center_letter='t',
  outer_letters=['a', 'c', 'f', 'k', 'o', 'r'],
  _answers=[P1_DUETTED, P1_TOOT, P1_TRACTOR])

GPUZZLE_2 = GPuzzle(
  date='2024-12-24',
  center_letter='t',
  outer_letters=['d', 'e', 'f', 'o', 'u', 'x'],
  _answers=[P2_CHAIR, P2_HORN, P2_PAGE, P2_RECLINE, P2_TOOT_, P2_TOOTED])

PUZZLES = [GPUZZLE_2, GPUZZLE_1]

GCLUE_PAGES = [
  GCluePage(url='/clue/beep', _answers=[P2_HORN, P2_PAGE, P1_TOOT, P2_TOOT_, P2_TOOTED]),
  GCluePage(url='/clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', _answers=[P1_TRACTOR]),
  GCluePage(url='/clue/play-together', _answers=[P1_DUETTED]),
  GCluePage(url='/clue/to-sit', _answers=[P2_CHAIR, P2_RECLINE])
]
ANSWERS = [P2_CHAIR, P1_DUETTED, P2_HORN, P2_PAGE, P2_RECLINE, P1_TOOT, P2_TOOT_, P2_TOOTED, P1_TRACTOR]
# PUZZLE_1 = {
#   "id": 9876,
#   "center_letter": "t",
#   "outer_letters": "acfkor",
#   "pangrams": [
#     "offtrack"
#   ],
#   "answers": [
#     "toot",
#     "tractor"
#   ],
#   "print_date": "2024-12-18",
#   "editor": "Sam Ezersky",
#   "clues": [
#     {
#       "word": "toot",
#       "text": "Beep",
#       "user": "SUCCINCTLY, STEVE G",
#       "url": "https://www.nytimes.com/2024/12/18/crosswords/spelling-bee-forum.html#permid=138370070"
#     },
#     {
#       "word": "tractor",
#       "text": "Dad preferred a John Deere ____ but grandpa loved his Ford.",
#       "user": "Jenn E",
#       "url": "https://www.nytimes.com/2024/12/18/crosswords/spelling-bee-forum.html#permid=138370266"
#     }
#   ]
# }
# PUZZLE_2 = {
#   "id": 1234,
#   "center_letter": "t",
#   "outer_letters": "defoux",
#   "pangrams": [
#     "outfoxed"
#   ],
#   "answers": [
#     "toot",
#     "tooted",
#     "tote",
#     "chair",
#     "recline"
#   ],
#   "print_date": "2024-12-24",
#   "clues": [
#     {
#       "word": "toot_",
#       "text": "Beep",
#       "user": "SUCCINCTLY, STEVE G",
#       "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506079"
#     },
#     {
#       "word": "tooted",
#       "text": "beep!!",
#       "user": "Kitt Richards 👩🏻‍💻💭",
#       "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506071"
#     },
#     {
#       "word": "tote",
#       "text": "beep",
#       "user": "Kalena G.",
#       "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506387"
#     },
#     {
#       "word": "chair",
#       "text": "to sit",
#       "user": "Kalena G.",
#       "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506387"
#     },
#     {
#       "word": "recline",
#       "text": "to sit",
#       "user": "Kenny G.",
#       "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506387"
#     }
#  ]
# }
