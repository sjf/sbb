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
class Pagination:
  # This is used on clues archive, it can be removed when this is changed.
  items: List[Any]
  page: int
  per_page: int

  @property
  def total_pages(self) -> int:
    return ceil(len(self.items) / self.per_page)

  @property
  def has_prev(self) -> bool:
    return self.page > 1

  @property
  def has_next(self) -> bool:
    return self.page < self.total_pages

  @property
  def prev_num(self) -> Optional[int]:
    return self.page - 1 if self.has_prev else None

  @property
  def next_num(self) -> Optional[int]:
    return self.page + 1 if self.has_next else None

  @property
  def start_index(self) -> int:
    return (self.page - 1) * self.per_page

  @property
  def end_index(self) -> int:
    return min(self.start_index + self.per_page, len(self.items))

  @property
  def visible_items(self) -> List[Any]:
    return self.items[self.start_index:self.end_index]

  @property
  def pages_to_display(self) -> List[int]:
    n = 3
    total_pages = self.total_pages
    if total_pages <= n*2:
      return list(range(1, total_pages + 1))

    # Show first n and last n pages
    first_part = list(range(1, n))
    last_part = list(range(total_pages - n - 1, total_pages + 1))
    return first_part + last_part

@dataclass
class PaginationBar:
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

