import json
from typing import List, Any, Dict, Optional, Tuple
from pyutils import *
from model import *

def get_clue_from_def(defs: GDefinitions) -> Optional[str]:
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

def get_prefix_hints(words: List[str]) -> List[Tuple[int,str]]:
  """ Returns a list hints relating to the prefixes/suffixes. They are scored by
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
      result.append((score, f"There are {count} words that {verb} with {smquote(prefix)}."))
  result = sorted(result, reverse=True)
  return result

def get_et(word: str, definition: GDefinition) -> str:
  return ''

def get_et_hints(answers: List[GAnswer]) -> List[Tuple[int,str]]:
  # for answer in answers:
  #   if not answer.definition:
  #     continue
  #   if not MW in answer.definition.source:
  #     continue
  #   et = get_et(answer.word, answer.definition)

  # result:List[Tuple[int,str]] = []
  # return result
  return []

def get_puzzle_hints(answers: List[GAnswer]) -> list:
  # answers = puzzle.answers
  hints = []

  # # Word length analysis
  # lengths = [len(word) for word in words]
  # most_common_length, count = Counter(lengths).most_common(1)[0]
  # hints.append(f"Many words in this puzzle are {most_common_length} letters long.")

  # Common prefixes and suffixes
  words = mapl(lambda x:x.word, answers)
  hints.extend(get_prefix_hints(words))
  hints.extend(get_et_hints(answers))
  # # Syllable structure analysis
  # syllable_counts = [len(re.findall(r'·', definitions[word]['hwi']['hw'])) + 1 for word in words if word in definitions and 'hwi' in definitions[word]]
  # if syllable_counts:
  #     most_common_syllable, count = Counter(syllable_counts).most_common(1)[0]
  #     hints.append(f"Many words in this puzzle have {most_common_syllable} syllables.")

  # # Common origins
  # origins = [definitions[word]['et'][0][1] for word in words if word in definitions and 'et' in definitions[word] and isinstance(definitions[word]['et'][0], list)]
  # if origins:
  #     most_common_origin, count = Counter(origins).most_common(1)[0]
  #     hints.append(f"Many words originate from {most_common_origin}.")

  # # Common fields of use
  # fields = [field for word in words if word in definitions and 'sls' in definitions[word] for field in definitions[word]['sls']]
  # if fields:
  #     most_common_field, count = Counter(fields).most_common(1)[0]
  #     hints.append(f"Several words are commonly used in {most_common_field} contexts.")
  print(hints)
  return hints

def parse_dict_entry(deff: GDefinition) -> None:
  fromm = deff.retrieved_from
  if "api.dictionaryapi.dev" in fromm:
    parse_wiktionary(deff)
  elif "dictionaryapi.com" in fromm:
    parse_mw(deff)
  else:
    raise Exception(f"Unhandled dict source {fromm}")

def parse_mw(deff: GDefinition) -> None:
  try:
    deff.source_url = f'https://www.merriam-webster.com/dictionary/{deff.word}'
    for o in deff.raw:
      td = GWordTypeDefinition(word_type = o['fl']) # functional label
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
                log_debug(f'Cant parse td text in MW for "{deff.word}"')
                failed_to_parse = True
              meaning = format_mw(dt[0][1])
              example = None
              vi = filterl(lambda x:x[0] == 'vis', sense['dt']) # Verbal Illustrations
              if vi:
                example = format_mw(vi[0][1][0].get('t', None), capitalize=False) # Just take first example
              if meaning:
                td.meanings.append(GWordMeaning(meaning = meaning, example = example))
        if failed_to_parse:
          # Just use the short definition.
          for meaning in o['shortdef']:
            if meaning:
              td.meanings.append(GWordMeaning(meaning = meaning, example = None))
      if td.meanings:
        # Keep the result if there were some parsed meanings.
        deff.word_types.append(td)
  except Exception as ex:
    # Just catch failures b/c the MW format is complex.
    log_debug(f"Can't parse MW entry for {deff.retrieved_from}", ex)

def parse_wiktionary(deff: GDefinition) -> None:
  # Wikitionary 3rd party API.
  deff.source_url = deff.raw[0]['sourceUrls'][0] # idk why there needs to be >1 source url.
  for sense in deff.raw:
    for m in sense.get('meanings',[]):
      td = GWordTypeDefinition(word_type = m['partOfSpeech'])
      deff.word_types.append(td)
      for d in m['definitions']:
        td.meanings.append(GWordMeaning(meaning = d['definition'], example = d.get('example',None)))

MW_FORMAT = [
  ('{ldquo}', '“'),
  ('{rdquo}', '”'),
  ('{inf}','<sub>'),
  ('{/inf}','</sub>'),
  ('{b}', '<bold>'),
  ('{/b}', '</bold>'),
  ('{sup}', '<sup>'),
  ('{/sup}', '</sup>'),
  ('{sc}', '<span style="font-variant: small-caps;">'),
  ('{/sc}','</span>'),
]
def format_mw(s: Optional[str], capitalize: bool=True) -> Optional[str]:
  # Replace Tokens Used in Running Text
  if not s:
    return s
  for pattern,replacement in MW_FORMAT:
    s = s.replace(pattern, replacement)
  # replace links: {d_link|linktext|}
  s = re.sub('\\{[a-z_]+\\|([^|:]+)[^}]*\\}', '\\1', s)
  s = re.sub('\\{[^}]+\\}','', s) # remove other formatting
  s = s.strip()
  if capitalize:
    s = s[0].upper() + s[1:]
  return s
