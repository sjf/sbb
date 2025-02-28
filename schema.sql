PRAGMA foreign_keys = ON;

CREATE TABLE puzzles (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,date DATE NOT NULL UNIQUE
  ,center_letter TEXT NOT NULL
  ,outer_letters TEXT NOT NULL
  ,hints TEXT NOT NULL -- JSON serialized List[Hints]
);

CREATE TABLE answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,word TEXT NOT NULL
  ,is_pangram BOOL NOT NULL
  ,puzzle_id INTEGER NOT NULL
  ,clue_id INTEGER
  ,FOREIGN KEY (puzzle_id) REFERENCES puzzles (id) ON DELETE CASCADE
  ,FOREIGN KEY (clue_id) REFERENCES clues (id) ON DELETE CASCADE
  ,UNIQUE(word, puzzle_id)
);

CREATE TABLE clues (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  -- Don't create duplicate rows for the same clue re-occuring.
  ,text TEXT NOT NULL UNIQUE
  -- Clues that only differ by punctuation etc. will have the same URL.
  -- So this column is not unique.
  ,url TEXT NOT NULL
);

CREATE TABLE definitions (
  word TEXT PRIMARY KEY
  ,definitions TEXT NOT NULL -- JSON serialized GDefinition
);

CREATE TABLE imported (
  name TEXT PRIMARY KEY
);

CREATE TABLE generated (
  path TEXT PRIMARY KEY
  ,lastmod TEXT NOT NULL
  ,needs_regen BOOL NOT NULL
);

