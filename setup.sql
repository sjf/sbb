CREATE TABLE puzzles (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,date DATE NOT NULL UNIQUE
  -- ,url TEXT NOT NULL UNIQUE -- Puzzle urls must be unique.
  ,center_letter TEXT NOT NULL
  ,outer_letters TEXT NOT NULL
);

CREATE TABLE answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,word TEXT NOT NULL
  ,is_pangram BOOL NOT NULL

  ,puzzle_id INTEGER NOT NULL
  ,clue_id INTEGER NOT NULL
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
  ,definition TEXT -- can be null if no defintion was found.
  ,source TEXT NOT NULL
);

