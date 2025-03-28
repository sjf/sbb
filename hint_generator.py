import json
import re
import random
import inflect
import mw
from typing import List, Any, Dict, Optional, Tuple
from pyutils import *
from model import *
from text_templates import *

inflect_engine = inflect.engine()

class HintGenerator:
  def __init__(self, puzzle: GPuzzle):
    self.puzzle = puzzle
    seed = int(hashlib.md5(puzzle.date.encode()).hexdigest(), 16)
    self.rng = random.Random(seed)

  def get_puzzle_hints(self) -> List[Hint]:
    hints = []
    answers = self.puzzle.answers
    words = mapl(lambda x:x.word, answers)
    hints.extend(self.get_prefix_hints(words))
    hints.extend(self.get_et_hints(answers))
    hints.extend(self.get_usage_hints(answers))
    hints = sorted(hints, reverse=True)
    return hints

  def get_prefix_hints(self, words: List[str], max_hints=4) -> List[Hint]:
    """ Returns a list of scored hints relating to the prefixes/suffixes. They are scored by
      the length of the prefix/suffix and the number of occurrences."""
    result = []
    for is_prefix in (True,False):
      prefix_counts = get_prefix_counts(words, is_prefix=is_prefix)
      if not prefix_counts:
        # Try shorter length of prefix
        prefix_counts = get_prefix_counts(words, is_prefix=is_prefix, min_length=3)
      if not prefix_counts:
        # Try fewer matches
        prefix_counts = get_prefix_counts(words, is_prefix=is_prefix, min_length=3, min_count=2)
      for prefix,count in prefix_counts.items():
        verb = 'start' if is_prefix else 'end'
        score = len(prefix) * count
        text = self.render_text(PREFIX_TEMPLATES, count=count, verb=verb, prefix=smquote(prefix))
        hint_words = filterl(lambda x:x.startswith(prefix) if is_prefix else x.endswith(prefix), words)
        result.append(Hint(score=score, text=text, words=hint_words))
    result = sorted(result, reverse=True)
    result = result[:max_hints]
    return result

  def get_et_hints(self, answers: List[GAnswer], min_count=2) -> List[Hint]:
    counter:Dict[str,int] = Counter()
    words:Dict[str,List[str]] = defaultdict(list)
    for answer in answers:
      lang = get_etymology(answer.definitions)
      if lang:
        counter[lang] += 1
        words[lang].append(answer.word)
    result = []
    for lang,count in counter.items():
      if count < min_count:
        continue
      score = sum(map(len, words[lang]))
      text = self.render_text(ET_TEMPLATES, count=count, lang=lang)
      result.append(Hint(score=score, text=text, words=words[lang]))
    result = sorted(result, reverse=True)
    return result

  def get_usage_hints(self, answers: List[GAnswer], min_count=1) -> List[Hint]:
    counter:Dict[str,int] = Counter()
    words:Dict[str,List[str]] = defaultdict(list)
    for answer in answers:
      usage = get_usage(answer.definitions)
      if not usage:
        continue
      counter[usage] += 1
      words[usage].append(answer.word)

    result = []
    for usage,count in counter.items():
      if count < min_count:
        continue
      score = sum(map(len, words[usage]))
      if count == 1:
        text = self.render_text(USAGE_TEMPLATES_SINGLE, count=count, usage=usage)
      else:
        text = self.render_text(USAGE_TEMPLATES, count=count, usage=usage)
      result.append(Hint(score=score, text=text, words=words[usage]))
    result = sorted(result, reverse=True)
    return result

  def render_text(self, templates, **params):
    t = self.rng.choice(templates)
    if 'count' in params:
      params['count'] = inflect_engine.number_to_words(params['count'])
    t = t.format(**params)
    t = t[0].upper() + t[1:]
    return t

def get_clue_from_def(defs: GDefinitions) -> Optional[str]:
  """ Create a clue for an answer when the NYT does not have one. """
  if not defs.has_def:
    return None
  # TODO: Don't produce clue text that contains the word.
  return defs.deff.word_types[0].meanings[0].meaning

def get_prefix_counts(words: List[str],
    is_prefix: bool=True,
    min_count: int=3,
    min_length: int=4,
    max_length: int=5) -> Dict[str,int]:
  """ Returns a mapping of prefix/suffix to the number of words where it occurs."""
  counter: Dict[str,int] = Counter()
  for word in words:
    for i in range(min_length, min(max_length+1, len(word))):  # Avoid single-letter prefixes
      prefix = word[:i] if is_prefix else  word[-i:]
      counter[prefix] += 1

  # Remove prefixes with too few counts
  # Remove prefixes that are words in the answer set.
  filtered = {}
  for prefix,count in counter.items():
    if count < min_count:
      continue
    if prefix in words:
      continue
    filtered[prefix] = count

  # Take the longest of each prefix.
  longest = {}
  for p1,count in filtered.items():
    has_longer = False
    for p2 in filtered.keys():
      is_fix = p2.startswith(p1) if is_prefix else p2.endswith(p1)
      if len(p2) > len(p1) and is_fix:
        has_longer = True
    if not has_longer:
      longest[p1] = count
  return longest

def get_tag_values(json_object: Any, target_key: str) -> List[str]:
  """ Get all the values in the JSON with the key `target_key. """
  result = []
  def parse_json_recursively(json_object, target_key):
    if type(json_object) is dict and json_object:
      for key in json_object:
        if key == target_key:
          val = json_object[key]
          result.append(val)
        parse_json_recursively(json_object[key], target_key)
    elif type(json_object) is list and json_object:
      for item in json_object:
        parse_json_recursively(item, target_key)
  parse_json_recursively(json_object, target_key)
  return result

def filter_et(et: str) -> bool:
  # Remove etmyologies of Middle English, unknown or cross-referenced.
  if et.startswith('{et_link|'):
    return False
  et = mw.format_mw(et)
  if et.lower().startswith('see '):
    return False
  if et.lower() == 'origin unknown':
    return False
  if et.startswith('Middle English'):
    return False
  return True

# Removed: Latin, French, English, German, Dutch, Greek
langs=['Abkhazian', 'Afrikaans', 'Akan', 'Albanian', 'Amharic', 'Arabic', 'Aragonese', 'Armenian', 'Assamese', 'Avaric', 'Avestan', 'Aymara', 'Azerbaijani',
'Bambara', 'Bashkir', 'Basque', 'Belarusian', 'Bengali', 'Bislama', 'Bosnian', 'Breton', 'Bulgarian', 'Burmese', 'Catalan', 'Valencian', 'Chamorro',
'Chechen', 'Chinese', 'Chuvash', 'Cornish', 'Corsican', 'Croatian', 'Czech', 'Danish', 'Divehi', 'Maldivian', 'Flemish', 'Dzongkha',
'Esperanto', 'Estonian', 'Faroese', 'Fijian', 'Finnish', 'Frisian', 'Fulah', 'Gaelic', 'Scottish', 'Scotts', 'Galician', 'Ganda', 'Georgian',
'Kalaallisut', 'Greenlandic', 'Guarani', 'Gujarati', 'Haitian', 'Creole', 'Hausa', 'Hebrew', 'Herero', 'Hindi', 'Hiri', 'Motu',
'Hungarian', 'Icelandic', 'Indonesian', 'Inuktitut', 'Inupiaq', 'Irish', 'Italian', 'Japanese', 'Javanese', 'Kannada', 'Kanuri', 'Kashmiri', 'Kazakh',
'Khmer', 'Kinyarwanda', 'Kirghiz', 'Kyrgyz', 'Kongo', 'Korean', 'Kurdish', 'Lao', 'Latvian', 'Limburgan', 'Lingala', 'Lithuanian', 'Luba-Katanga',
'Luxembourgish', 'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Manx', 'Maori', 'Marathi', 'Marshallese', 'Mongolian', 'Nauru', 'Navajo',
'Navaho', 'Ndebele', 'Ndonga', 'Nepali', 'Norwegian', 'Occitan', 'Ojibwa', 'Oriya', 'Ossetian', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi',
'Quechua', 'Romanian', 'Moldavian', 'Romansh', 'Russian', 'Sami', 'Samoan', 'Sango', 'Sanskrit', 'Sardinian', 'Serbian', 'Shona', 'Sindhi', 'Sinhala',
'Slovak', 'Slovenian', 'Somali', 'Sotho', 'Spanish', 'Sundanese', 'Swahili', 'Swedish', 'Tagalog', 'Tahitian', 'Tajik', 'Tamil', 'Tatar', 'Telugu', 'Thai',
'Tibetan', 'Tigrinya', 'Tonga', 'Tsonga', 'Tswana', 'Turkish', 'Turkmen', 'Uighur', 'Uyghur', 'Ukrainian', 'Urdu', 'Uzbek', 'Venda', 'Vietnamese', 'Walloon',
'Welsh', 'Wolof', 'Xhosa', 'Sichuan', 'Yiddish', 'Yoruba', 'Zhuang', 'Chuang', 'Zulu']
def get_lang_from_et(et: str) -> Optional[str]:
  positions = []
  for lang in langs:
    match = re.search(rf'\b{lang}\b', mw.format_mw(et), re.IGNORECASE)
    if match:
      positions.append((match.start(),lang))
  positions = sorted(positions)
  if positions:
    return positions[0][1] # Get the lang that occurred first.
  return None

def get_etymology(defs: GDefinitions) -> Optional[str]:
  if not defs.mw:
    return None
  ets = get_tag_values(defs.mw.raw, 'et')
  # The etymology is in the form [['text', 'actual description etc']]
  ets = mapl(lambda x:x[0][1], ets)
  ets = filterl(filter_et, ets)
  for et in ets:
    lang = get_lang_from_et(et)
    if lang:
      # Return the first detected language.
      return lang
  return None

def get_usage(defs: GDefinitions, max_usages=3) -> Optional[str]:
  if not defs.mw:
    return None
  usages = get_tag_values(defs.mw.raw, 'sls')
  if len(usages) > max_usages:
    # Too many usages means most are bogus.
    return None
  usages = filterl(filter_usage, usages)
  usage = mapl(lambda x:x[0], usages)
  if usage:
    return usage[0]
  return None

def filter_usage(usage: List[str]) -> bool:
  # result = []
  # whitelist = ['law', 'gardening', 'anatomy','of a ship','of a playing card','medical','baseball','of an airplane',
  # 'of fish','mathematics','psychoanalytic theory','botany']
  whitelist = [['law'], ['gardening'], ['anatomy'], ['mathematics']]
  # if 'law' in usage:
  #   return joinl(usage, sep=' ')
  # if 'gardening' in usage
  for w in whitelist:
    if usage == w:
      # if w in usage and not 'informal' in usage:
      return True
  return False
  # denylist = ['informal','vulgar','archaic','British','Scottish', 'dialectal', 'Scotland','obsolete','dated','dialect','slang','literary','formal']
  # for part in usage:
  #   for word in denylist:
  #     if word in part:
  #       return False
  # if usage == ['US']:
  #   return False
  # return True

