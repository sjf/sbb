CREATE TABLE puzzles (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,date DATE NOT NULL UNIQUE
  -- ,url TEXT NOT NULL UNIQUE -- Puzzle urls must be unique.
  ,center_letter TEXT NOT NULL
  ,outer_letters TEXT NOT NULL
  ,answers TEXT NOT NULL -- The answers are just listed here instead of fully normalizing.
  ,pangrams TEXT NOT NULL
);

CREATE TABLE clues (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  -- ,url TEXT NOT NULL UNIQUE -- Clue urls must be unique.
  ,text TEXT NOT NULL UNIQUE -- The clue text may reoccur for different answers.
);

CREATE TABLE answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,answer TEXT NOT NULL
  ,puzzle_id INTEGER NOT NULL
  ,FOREIGN KEY (puzzle_id) REFERENCES puzzles (id) ON DELETE CASCADE
  ,UNIQUE(answer, puzzle_id)
);

CREATE TABLE puzzle_clues (
  -- Each puzzle has many clues
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,puzzle_id INTEGER
  ,clue_id INTEGER
  ,FOREIGN KEY (puzzle_id) REFERENCES puzzles (id) ON DELETE CASCADE
  ,FOREIGN KEY (clue_id) REFERENCES clues (id) ON DELETE CASCADE
  -- The same puzzle can have the same clue more than once.
  -- So dont use this unique constraint.
  -- ,UNIQUE(puzzle_id, clue_id)
);

CREATE TABLE clue_answers (
  -- Each clue may have more than answer.
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,clue_id INTEGER
  ,answer_id INTEGER
  ,FOREIGN KEY (clue_id) REFERENCES clues (id) ON DELETE CASCADE
  ,FOREIGN KEY (answer_id) REFERENCES answer (id) ON DELETE CASCADE
  ,UNIQUE(clue_id, answer_id)
);

CREATE TABLE urls (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,url TEXT UNIQUE
);

CREATE TABLE url_clues (
  -- Some clues have the same URL.
  id INTEGER PRIMARY KEY AUTOINCREMENT
  ,url_id INTEGER
  ,clue_id INTEGER
  ,FOREIGN KEY (url_id) REFERENCES urls (id) ON DELETE CASCADE
  ,FOREIGN KEY (clue_id) REFERENCES clues (id) ON DELETE CASCADE
  ,UNIQUE(url_id, clue_id)
);


-- CREATE TABLE definitions (
--   id INTEGER PRIMARY KEY,
--   word TEXT NOT NULL,
--   definition TEXT NOT NULL
-- );

