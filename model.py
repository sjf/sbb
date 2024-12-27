from dataclasses import dataclass, asdict, fields, field
from typing import List, Any, Dict, Optional

# Generator dataclasses
@dataclass(order=True)
class GAnswer:
  puzzle_date: str
  answer: str

@dataclass(order=True)
class GClue:
  id: int = field(compare=False)
  text: str
  _answers: List[GAnswer] = field(default_factory=list)
  @property
  def answers(self) -> List[GAnswer]:
    return sorted(self._answers)
  def add_answer(self, answer: GAnswer):
    self._answers.append(answer)

@dataclass(order=True)
class GPuzzleClue:
  answer: str
  text: str

@dataclass
class GPuzzle:
  id: int
  date: str
  center_letter: str
  outer_letters: List[str]
  answers: List[str]
  pangrams: List[str]
  _clues: List[GPuzzleClue] = field(default_factory=list)

  @property
  def clues(self) -> List[GPuzzleClue]:
    return sorted(self._clues)
  def add_clue(self, clue: GPuzzleClue):
    self._clues.append(clue)
  def __lt__(self, other):
    return self.date > other.date # reverse date sort

@dataclass
class GCluePage:
  id: int
  url: str
  _clues: List[GClue] = field(default_factory=list)
  @property
  def clues(self) -> List[GClue]:
    return sorted(self._clues)
