import json
from dataclasses import dataclass, asdict, fields, field
import datetime
from typing import List, Any, Dict, Optional
from mbutils import *

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
@dataclass(order=True)
class GClue:
  text: str
  url: str

@dataclass
class GAnswer:
  word: str
  is_pangram: bool
  text: str
  url: str # URL of the clue page for this answer, multiple answers can have the same url.
  puzzle_date: str
  definition: Optional[GDefinition]
  def __lt__(self, other):
    if self.word == other.word:
      return self.puzzle_date > other.puzzle_date # reverse date sort

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

  def __lt__(self, other):
    return self.date > other.date # reverse date sort

@dataclass
class GCluePage:
  url: str
  _answers: List[GAnswer] = field(default_factory=list)
  @property
  def answers(self) -> List[GAnswer]:
    return sorted(self._answers)

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

def date_format(value: str) -> str:
    date = datetime.datetime.strptime(value, "%Y-%m-%d")
    return date.strftime("%B %d, %Y")
