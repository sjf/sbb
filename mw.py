import json
from typing import List, Any, Dict, Optional, Tuple
from functools import lru_cache
from pyutils import *
from model import *

def get_prefix_counts(words: List[str],
    is_prefix: bool=True,
    min_count: int=3,
    min_length: int=4,
    max_length: int=5) -> Dict[str,int]:
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

def prefix_hints(words: List[str]) -> List[Tuple[int,str]]:
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

def get_puzzle_hints(answers: List[GAnswer]) -> list:
  # answers = puzzle.answers
  hints = []

  # # Word length analysis
  # lengths = [len(word) for word in words]
  # most_common_length, count = Counter(lengths).most_common(1)[0]
  # hints.append(f"Many words in this puzzle are {most_common_length} letters long.")

  # Common prefixes and suffixes
  words = mapl(lambda x:x.word, answers)
  hints.extend(prefix_hints(words))

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


@lru_cache(maxsize=None)
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
                  example = format_mw(vi[0][1][0].get('t', None), capitalize=False) # Just take first example
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
