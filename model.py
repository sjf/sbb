import json
from dataclasses import dataclass, asdict, fields, field
import datetime
from typing import List, Any, Dict, Optional
from math import ceil
from functools import lru_cache
from pyutils import *

# Dictionary dataclasses.
@dataclass
class GWordMeaning:
  meaning: str
  example: Optional[str] = None

@dataclass
class GWordTypeDefinition:
  word_type: str # type of word, e.g. noun, verb
  meanings: List[GWordMeaning] = field(default_factory=list)

@dataclass
class GDefinition:
  word: str
  retrieved_on: str
  retrieved_from: str # The API endpoint.
  raw: Any # The unparsed json received from the API.

  # These are only present if the definition was parsed
  source_url: Optional[str] = None # Attribution URL
  # Parsed definition, ready for frontend.
  word_types: List[GWordTypeDefinition] = field(default_factory=list)

  @property
  def is_mw(self) -> bool:
    return "https://dictionaryapi.com" in self.retrieved_from

  @property
  def parsed(self) -> bool:
    # Was parsed correctly.
    return bool(self.word_types)

  @property
  def source(self) -> Optional[str]:
    # Attribution name (different than the API endpoint)
    if not self.source_url:
      return None
    return url_domain(self.source_url)

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    l = []
    for field in fields(self):
      max_len = 10
      val = getattr(self, field.name)
      if field.name == 'raw' and val:
        val = repr(val)[:max_len-3] + '...'
      l.append(f'{field.name}={val}')
    l.append(f'is_mw={self.is_mw}')
    l.append(f'parsed={self.parsed}')
    return f"GDefinition({joinl(l, sep=', ')})"


@dataclass
class GDefinitions:
  word: str
  defs: List[GDefinition]
  @property
  def deff(self) -> GDefinition:
    for d in self.defs:
      if d.is_mw and d.parsed:
        # Prefer MW results
        return d
    for d in self.defs:
      # Otherwise, return first parsed entry.
      if d.parsed:
        return d
    raise Exception(f"No definition for {self.word}")
  @property
  def has_def(self) -> bool:
    # At least one prased definition.
    return bool(filterl(lambda x:x.parsed, self.defs))
  @property
  def mw(self) -> Optional[GDefinition]:
    for d in self.defs:
      if d.is_mw and d.parsed:
        return d
    return None

# Game dataclasses.
@dataclass
class GAnswer:
  word: str # The answer word.
  is_pangram: bool
  text: Optional[str] # Clue text.
  url: Optional[str] # URL of the clue page for this answer, multiple answers can have the same url.
  puzzle_date: str
  definitions: GDefinitions
  def __lt__(self, other):
    if self.word == other.word:
      return self.puzzle_date > other.puzzle_date
    return self.word < other.word

@dataclass
class Hint:
  score: int
  text: str
  words: List[str]
  def __lt__(self, other):
    return (self.score, self.text, self.words) < (other.score, other.text, other.words)

@dataclass
class GPuzzle:
  date: str # Date in the format YYYY-MM-DD.
  center_letter: str
  outer_letters: List[str]
  hints: List[Hint]
  _answers: List[GAnswer] = field(default_factory=list)

  @property
  def answers(self) -> List[GAnswer]:
    return sorted(self._answers)
  def add_answer(self, answer: GAnswer):
    self._answers.append(answer)
  def answer_list(self) -> str:
    return joinl(mapl(lambda x:x.word, self.answers), sep=',')
  def has_all_clues(self):
    n = len(list(filter(lambda x:x.text and x.url and x.url.startswith('/clue/'), self._answers)))
    return n/len(self._answers) > .8 # 80% of answers have official clues.

  def __lt__(self, other):
    return self.date > other.date

@dataclass
class GClueAnswer:
  word: str # The answer word.
  text: Optional[str] # Clue text.
  puzzle_dates: list[str] # The dates on which this clue/anwer combo appeared.
  # The same clue can hava different answers.
  definitions: GDefinitions
  def __lt__(self, other):
    if self.word == other.word:
      return self.puzzle_dates > other.puzzle_dates
    return self.word < other.word

@dataclass
class GCluePage:
  url: str
  _clue_answers: List[GClueAnswer] = field(default_factory=list)
  @property
  def clue_answers(self) -> List[GClueAnswer]:
    return sorted(self._clue_answers, reverse=True)
  @property
  def lastmod(self) -> str:
    # Most recent usage of this clue.
    return self.clue_answers[0].puzzle_dates[0]
  def __lt__(self, other):
    return (self.url, self.clue_answers) < (other.url, other.clue_answers)

@dataclass
class GWordDefinition:
  word: str
  definition: Optional[GDefinition]
  def __lt__(self, other):
    return self.word < other.word

@dataclass
class GSearchResult:
  word: str
  text: str
  url: str
  lastused: str
  def __lt__(self, other):
    if self.word == other.word:
      return self.text > other.text

def format_yearmonth(value: str) -> str:
  date = datetime.datetime.strptime(value, "%Y-%m")
  return date.strftime("%B, %Y")

@dataclass
class PaginateList:
  """ Creates pagination links for page from a list of URLs. """
  pages: List[str] # List of the urls in order.
  current: str # The url of the current page.

  @property
  def total_pages(self) -> int:
    return len(self.pages)

  @property
  def _idx(self) -> int:
    """ Index of current page (starting at zero) """
    try:
      idx = self.pages.index(self.current)
    except ValueError:
      raise Exception(f"Cannot paginate, {self.current} not in pages: {joinl(self.pages, sep=',')}")
    return idx

  @property
  def page(self) -> int:
    return self._idx + 1

  @property
  def has_prev(self) -> bool:
    return self._idx > 0

  @property
  def has_next(self) -> bool:
    return self._idx < self.total_pages - 1

  @property
  def first(self) -> str:
    return self.pages[0]

  @property
  def last(self) -> str:
    return self.pages[-1]

  @property
  def prev(self) -> Optional[str]:
    return self.pages[self._idx - 1] if self.has_prev else None

  @property
  def next(self) -> Optional[str]:
    return self.pages[self._idx + 1] if self.has_next else None

@dataclass
class PaginateByNum:
  """ Creates pagination links for numbered pages. """

  current: int # Current page number
  has_next: bool
  base_url: str

  @property
  def page(self) -> int:
    return self.current

  @property
  def has_prev(self) -> bool:
    return self.current > 1

  @property
  def prev(self) -> Optional[str]:
    if not self.has_next:
      return None
    if self.current == 2:
      # Don't use page=1
      return self.base_url
    return replace_url_param(self.base_url, 'page', self.current - 1)

  @property
  def next(self) -> Optional[str]:
    if not self.has_next:
      return None
    return replace_url_param(self.base_url, 'page', self.current + 1)

  @property
  def first(self) -> str:
    return self.base_url

  @property
  def last(self) -> Optional[str]:
    return None

  @property
  def total_pages(self) -> Optional[int]:
    return None

