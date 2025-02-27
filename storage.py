from typing import List, Any, Dict, Optional
from dataclasses import dataclass

# Storage classes, generated from the schema.
@dataclass
class Puzzle:
  date: str
  center_letter: str
  outer_letters: List[str]
  hints: str
  id: Optional[int] = None

@dataclass
class Answer:
  word: str
  is_pangram: bool
  puzzle_id: int
  clue_id: Optional[int]
  id: Optional[int] = None

@dataclass
class Clue:
  text: str
  url: str
  id: Optional[int] = None

@dataclass
class Definition:
  word: str
  # JSON serialized GDefinitions
  definitions: str
