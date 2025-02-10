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
  def __lt__(self, other):
    if self.word == other.word:
      return self.text > other.text

def dictapis_to_def(word: str, content: str, source: str) -> Optional[GDefinition]:
  if not source or not content:
    return None
  if "api.dictionaryapi.dev" in source:
    # Wikitionary 3rd party API.
    obj = json.loads(content)
    url = source_url=obj[0]['sourceUrls'][0] # idk why there needs to be >1 source url.
    result = GDefinition(word=word, source_url=url, source=url_domain(url))
    for sense in obj:
      for m in sense.get('meanings',[]):
        td = GWordTypeDefinition(word_type = m['partOfSpeech'])
        result.word_types.append(td)
        for d in m['definitions']:
          td.meanings.append(GWordMeaning(meaning = d['definition'], example = d.get('example',None)))
    return result
  if "dictionaryapi.com" in source:
    # print(content, source)
    try:
      obj = json.loads(content)
      url = f'https://www.merriam-webster.com/dictionary/{word}'
      result = GDefinition(word=word, source_url=url, source=url_domain(url))
      for o in obj:
        td = GWordTypeDefinition(word_type = o['fl']) # functional label
        result.word_types.append(td)
        failed_to_parse = False
        for d in o['def']: # definition
          for s in d['sseq']: # sense
            for subsense in s:
              if subsense[0] == 'sense':
                sense = subsense[1]
                usage = sense.get('sls', []) # Subject/Status Labels
                dt = filterl(lambda x:x[0] == 'text', sense['dt']) # Defining Text
                uns = filterl(lambda x:x[0] == 'uns', sense['dt']) # Usage note
                if not dt and len(uns) == 1:
                  dt = filterl(lambda x:x[0] == 'text', uns[0][1][0])
                if not len(dt) == 1:
                  log_error(f'Cant parse td text in MW for "{word}"')
                  failed_to_parse = True
                meaning = format_mw(dt[0][1])
                example = None
                vi = filterl(lambda x:x[0] == 'vis', sense['dt']) # Verbal Illustrations
                if vi:
                  example = format_mw(vi[0][1][0].get('t', None)) # Just take first example
                if meaning:
                  td.meanings.append(GWordMeaning(meaning = meaning, example = example))
          if failed_to_parse:
            # Just use the short definition.
            for meaning in o['shortdef']:
              if meaning:
                td.meanings.append(GWordMeaning(meaning = meaning, example = None))
      return result
    except Exception as e: # Just catch failures b/c the MW format is complex.
      log_error(f"Can't parse MW entry for {source}")
  return None

MW_FORMAT = [
  ('{ldquo}', '“'),
  ('{rdquo}', '”'),
  ('{inf}','<sub>'),
  ('{\\/inf}','</sub>'),
  ('{b}', '<bold>'),
  ('{\\/b}', '</bold>'),
  ('{sup}', '<sup>'),
  ('{\\/sup}', '</sup>'),
  ('{sc}', '<span style="font-variant: small-caps;">'),
  ('{\\/sc}','</span>'),
]
def format_mw(s: Optional[str]) -> Optional[str]:
  # Replace Tokens Used in Running Text
  if not s:
    return s
  for pattern,replacement in MW_FORMAT:
    s = s.replace(pattern, replacement)
  # replace links: {d_link|linktext|}
  s = re.sub('\\{[a-z_]+\\|([^|:]+)[^}]*\\}', '\\1', s)
  s = re.sub('\\{[^}]+\\}','', s) # remove other formatting
  s = s.strip()
  return s

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

