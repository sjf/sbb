import json
import re
from typing import List, Any, Dict, Optional, Tuple
from pyutils import *
from model import *

def get_clue_from_def(defs: GDefinitions) -> Optional[str]:
  """ Create a clue for an answer when the NYT does not have one. """
  if not defs.has_def:
    return None
  # TODO: Don't produce clue text that contains the word.
  return defs.deff.word_types[0].meanings[0].meaning

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
def format_mw(s: Optional[str], capitalize: bool=True) -> str:
  # Replace Tokens Used in Running Text
  if not s:
    return ''
  for pattern,replacement in MW_FORMAT:
    s = s.replace(pattern, replacement)
  # replace links: {d_link|linktext|}
  s = re.sub('\\{[a-z_]+\\|([^|:]+)[^}]*\\}', '\\1', s)
  s = re.sub('\\{[^}]+\\}','', s) # remove other formatting
  s = s.strip()
  if capitalize:
    s = s[0].upper() + s[1:]
  return s


