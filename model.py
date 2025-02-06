import json
from dataclasses import dataclass, asdict, fields, field
import datetime
from typing import List, Any, Dict, Optional
from math import ceil
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
  source: str # Attribution name
  source_url: str
  word_types: List[GWordTypeDefinition] = field(default_factory=list)

# Game dataclasses.
@dataclass
class GAnswer:
  word: str # The answer word.
  is_pangram: bool
  text: Optional[str] # Clue text.
  url: Optional[str] # URL of the clue page for this answer, multiple answers can have the same url.
  puzzle_date: str
  definition: Optional[GDefinition]
  def __lt__(self, other):
    if self.word == other.word:
      return self.puzzle_date > other.puzzle_date
    return self.word < other.word

@dataclass
class GPuzzle:
  date: str # Date in the format YYYY-MM-DD.
  center_letter: str
  outer_letters: List[str]
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
  definition: Optional[GDefinition]
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
    return sorted(self._clue_answers)

@dataclass
class GSearchResult:
  word: str
  text: str
  url: str
  def __lt__(self, other):
    if self.word == other.word:
      return self.text > other.text

def dictapis_to_def(content: str, source: str) -> Optional[GDefinition]:
  if not source or not content:
    return None
  if "api.dictionaryapi.dev" in source:
    obj = json.loads(content)
    url = source_url=obj[0]['sourceUrls'][0] # idk why there needs to be >1 source url.
    result = GDefinition(word=obj[0]['word'], source_url=url, source=url_domain(url))
    for word in obj:
      for m in word.get('meanings',[]):
        td = GWordTypeDefinition(word_type = m['partOfSpeech'])
        result.word_types.append(td)
        for d in m['definitions']:
          td.meanings.append(GWordMeaning(meaning = d['definition'], example = d.get('example',None)))
    return result
  # todo handle merrian webster entries
  return None

def format_date(value: str) -> str:
  date = datetime.datetime.strptime(value, "%Y-%m-%d")
  return date.strftime("%B %-d, %Y")

def format_yearmonth(value: str) -> str:
  date = datetime.datetime.strptime(value, "%Y-%m")
  return date.strftime("%B, %Y")

def sort_by_clue(answers: List[GAnswer]) -> List[GAnswer]:
  return sorted(answers, key=lambda x: (x.word[0], len(x.word)))

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
    idx = self.pages.index(self.current)
    if idx == -1:
      raise Exception(f"Cannot paginate, {self.current} not in pages.")
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

