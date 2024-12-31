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


# GPUZZLE_1 = GPuzzle(id=9876, date='2024-12-18',
#       center_letter='t', outer_letters=['a', 'c', 'f', 'k', 'o', 'r'],
#       answers=['toot', 'tractor'], pangrams=['offtrack'],
#       _clues=[
#         GPuzzleClue(answer='toot', text='Beep'),
#         GPuzzleClue(answer='tractor', text='Dad preferred a John Deere ____ but grandpa loved his Ford.')
#       ])
# GPUZZLE_2 = GPuzzle(id=1234,
#       date='2024-12-24',
#       center_letter='t',
#       outer_letters=['d', 'e', 'f', 'o', 'u', 'x'],
#       answers=['toot', 'tooted', 'tote', 'chair', 'recline'],
#       pangrams=['outfoxed'],
#       _clues=[
#         GPuzzleClue(answer='toot_', text='Beep'),
#         GPuzzleClue(answer='tooted', text='beep!!'),
#         GPuzzleClue(answer='tote', text='beep'),
#         GPuzzleClue(answer='chair', text='to sit'),
#         GPuzzleClue(answer='recline', text='to sit')
#       ])
# ANSWERS = [
#   GClue(id=1, text='Beep', _answers=[
#     GAnswer(puzzle_date='2024-12-18', answer='toot', definition=None),
#     GAnswer(puzzle_date='2024-12-24', answer='toot_', definition=None)
#   ]),
#   GClue(id=2, text='Dad preferred a John Deere ____ but grandpa loved his Ford.', _answers=[
#     GAnswer(puzzle_date='2024-12-18', answer='tractor', definition=None)]),
#   GClue(id=4, text='beep!!', _answers=[GAnswer(puzzle_date='2024-12-24', answer='tooted', definition=None)]),
#   GClue(id=5, text='beep', _answers=[GAnswer(puzzle_date='2024-12-24', answer='tote', definition=None)]),
#   GClue(id=6, text='to sit', _answers=[
#     GAnswer(puzzle_date='2024-12-24', answer='chair', definition=None),
#     GAnswer(puzzle_date='2024-12-24', answer='recline', definition=None)
#   ])
# ]
GCLUE_PAGES = [
  GCluePage(url='clue/play-together', _answers=[
    GAnswer(word='duetted', is_pangram=False, text='Play together', url='clue/play-together', puzzle_date='2024-12-18', definition=None)]),
  GCluePage(url='clue/beep', _answers=[
    GAnswer(word='toot', is_pangram=False, text='Beep', url='clue/beep', puzzle_date='2024-12-18', definition=None),
    GAnswer(word='toot_', is_pangram=False, text='Beep', url='clue/beep', puzzle_date='2024-12-24', definition=None),
    GAnswer(word='tooted', is_pangram=False, text='beep!!', url='clue/beep', puzzle_date='2024-12-24', definition=None),
    GAnswer(word='horn', is_pangram=False, text='beep', url='clue/beep', puzzle_date='2024-12-24', definition=None),
    GAnswer(word='page', is_pangram=False, text='beep', url='clue/beep', puzzle_date='2024-12-24', definition=None)]),
  GCluePage(url='clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', _answers=[
    GAnswer(word='tractor', is_pangram=False, text='Dad preferred a John Deere ____ but grandpa loved his Ford.',
      url='clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', puzzle_date='2024-12-18', definition=None)]),
  GCluePage(url='clue/to-sit', _answers=[
    GAnswer(word='chair', is_pangram=False, text='to sit', url='clue/to-sit', puzzle_date='2024-12-24', definition=None),
    GAnswer(word='recline', is_pangram=False, text='to sit', url='clue/to-sit', puzzle_date='2024-12-24', definition=None)])
]
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
