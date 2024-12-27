#!/usr/bin/env python3
import os
import pytest
import json
import db
import tempfile
from mbutils import *
from importer import *

def setup(fs, monkeypatch):
  fs.pause()
  schema = read('setup.sql')
  fd, temp_db = tempfile.mkstemp() # sqlite cannot use pyfakefs
  os.close(fd)
  fs.resume()
  monkeypatch.setattr(db, 'DB_FILE', temp_db)
  write('setup.sql', schema)
  mkdir('scraped')
  mkdir('archive')
  write(FILE_1, json.dumps(PUZZLE_1))
  write(FILE_2, json.dumps(PUZZLE_2))
  return temp_db

def tear_down(fs, temp_db):
  fs.pause()
  rm(temp_db)
  fs.resume()

def test_import_succeeds(fs, monkeypatch):
  temp_db = setup(fs, monkeypatch)
  try:
    importer = Importer()
    importer.import_files([FILE_1, FILE_2])

    puzzles = importer.db.fetch_gpuzzles()
    assert puzzles == [GPUZZLE_1, GPUZZLE_2]
    latest = importer.db.fetch_latest_gpuzzle()
    assert latest == GPUZZLE_2
    clues = importer.db.fetch_gclues()
    assert clues == GCLUES
    clue_pages = importer.db.fetch_gclue_pages()
    print(clue_pages)
    assert clue_pages == GCLUE_PAGES
    # assert not exists(FILE_1)
    # assert not exists(FILE_2)
    # assert exists("archive/" + basename(FILE_1))
    # assert exists("archive/" + basename(FILE_2))
  finally:
    tear_down(fs, temp_db)


def test_re_import_succeeds(fs, monkeypatch):
  temp_db = setup(fs, monkeypatch)
  try:
    importer = Importer()
    importer.import_files([FILE_1, FILE_2], archive=False)
    importer.import_files([FILE_1, FILE_2])

    assert importer.db.fetch_gpuzzles() == [GPUZZLE_1, GPUZZLE_2]
    assert importer.db.fetch_gclues() == GCLUES
  finally:
    tear_down(fs, temp_db)

FILE_1 = 'scraped/9876.json'
FILE_2 = 'scraped/1234.json'

GPUZZLE_1 = GPuzzle(id=9876, date='2024-12-18',
      center_letter='t', outer_letters=['a', 'c', 'f', 'k', 'o', 'r'],
      answers=['toot', 'tractor'], pangrams=['offtrack'],
      _clues=[
        GPuzzleClue(answer='toot', text='Beep'),
        GPuzzleClue(answer='tractor', text='Dad preferred a John Deere ____ but grandpa loved his Ford.')
      ])
GPUZZLE_2 = GPuzzle(id=1234,
      date='2024-12-24',
      center_letter='t',
      outer_letters=['d', 'e', 'f', 'o', 'u', 'x'],
      answers=['toot', 'tooted', 'tote', 'chair', 'recline'],
      pangrams=['outfoxed'],
      _clues=[
        GPuzzleClue(answer='toot_', text='Beep'),
        GPuzzleClue(answer='tooted', text='beep!!'),
        GPuzzleClue(answer='tote', text='beep'),
        GPuzzleClue(answer='chair', text='to sit'),
        GPuzzleClue(answer='recline', text='to sit')
      ])
GCLUES = [
  GClue(id=1, text='Beep', _answers=[
    GAnswer(puzzle_date='2024-12-18', answer='toot'),
    GAnswer(puzzle_date='2024-12-24', answer='toot_')
  ]),
  GClue(id=2, text='Dad preferred a John Deere ____ but grandpa loved his Ford.', _answers=[
    GAnswer(puzzle_date='2024-12-18', answer='tractor')]),
  GClue(id=4, text='beep!!', _answers=[GAnswer(puzzle_date='2024-12-24', answer='tooted')]),
  GClue(id=5, text='beep', _answers=[GAnswer(puzzle_date='2024-12-24', answer='tote')]),
  GClue(id=6, text='to sit', _answers=[
    GAnswer(puzzle_date='2024-12-24', answer='chair'),
    GAnswer(puzzle_date='2024-12-24', answer='recline')
  ])
]
GCLUE_PAGES = [
  GCluePage(id=1, url='clue/beep', _clues=[GCLUES[0], GCLUES[2], GCLUES[3]]),
  GCluePage(id=2, url='clue/dad-preferred-a-john-deere-but-grandpa-loved-his-ford', _clues=[GCLUES[1]]),
  GCluePage(id=6, url='clue/to-sit', _clues=[GCLUES[4]]),
]

PUZZLE_1 = {
  "id": 9876,
  "center_letter": "t",
  "outer_letters": "acfkor",
  "pangrams": [
    "offtrack"
  ],
  "answers": [
    "toot",
    "tractor"
  ],
  "print_date": "2024-12-18",
  "editor": "Sam Ezersky",
  "clues": [
    {
      "word": "toot",
      "text": "Beep",
      "user": "SUCCINCTLY, STEVE G",
      "url": "https://www.nytimes.com/2024/12/18/crosswords/spelling-bee-forum.html#permid=138370070"
    },
    {
      "word": "tractor",
      "text": "Dad preferred a John Deere ____ but grandpa loved his Ford.",
      "user": "Jenn E",
      "url": "https://www.nytimes.com/2024/12/18/crosswords/spelling-bee-forum.html#permid=138370266"
    }
  ]
}
PUZZLE_2 = {
  "id": 1234,
  "center_letter": "t",
  "outer_letters": "defoux",
  "pangrams": [
    "outfoxed"
  ],
  "answers": [
    "toot",
    "tooted",
    "tote",
    "chair",
    "recline"
  ],
  "print_date": "2024-12-24",
  "clues": [
    {
      "word": "toot_",
      "text": "Beep",
      "user": "SUCCINCTLY, STEVE G",
      "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506079"
    },
    {
      "word": "tooted",
      "text": "beep!!",
      "user": "Kitt Richards 👩🏻‍💻💭",
      "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506071"
    },
    {
      "word": "tote",
      "text": "beep",
      "user": "Kalena G.",
      "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506387"
    },
    {
      "word": "chair",
      "text": "to sit",
      "user": "Kalena G.",
      "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506387"
    },
    {
      "word": "recline",
      "text": "to sit",
      "user": "Kenny G.",
      "url": "https://www.nytimes.com/2024/12/24/crosswords/spelling-bee-forum.html#permid=138506387"
    }
 ]
}
