import json
import re
from typing import List, Any, Dict, Optional, Tuple
from pyutils import *
from model import *

DEBUG = config['DEBUG']

def parse_mw(deff: GDefinition) -> None:
  try:
    # This is the link to the human readable MW page.
    deff.source_url = f'https://www.merriam-webster.com/dictionary/{deff.word}'
    for hom in deff.raw:
      fl = hom.get('fl', None)  # functional label
      if not fl:
        # No word type, can't handle this.
        continue
      td = GWordTypeDefinition(word_type = fl)
      failed_to_parse = False
      for d in hom['def']: # definition
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
          for meaning in hom['shortdef']:
            if meaning:
              td.meanings.append(GWordMeaning(meaning = meaning, example = None))
      if td.meanings:
        # Keep the result if there were some parsed meanings.
        deff.word_types.append(td)
  except Exception as ex:
    # Just catch failures b/c the MW format is complex.
    log(f"Can't parse MW entry for {deff.retrieved_from}", ex)

def get_clue_from_def(defs: GDefinitions) -> Optional[str]:
  """ Create a clue for an answer when the NYT does not have one. """
  if not defs.has_def:
    return None
  # TODO: Don't produce clue text that contains the word.
  return defs.deff.word_types[0].meanings[0].meaning

def is_good(defs: GDefinitions) -> Tuple[bool, Optional[str]]:
  if not defs.mw:
    return False, 'No MW'

  banned = ['abbreviation', 'combining form', 'biographical name', 'trademark', 'geographical name', 'prefix']
  def is_banned(wt: str) -> bool:
    return wt in banned or 'phrase' in wt.lower()

  types = [wt.word_type for wt in defs.mw.word_types]
  good = filterl(lambda t:not(is_banned(t)), types)
  bad = filterl(is_banned, types)
  # if bad and good:
  DEBUG and print(f'{defs.word} {bad} {good}')
  if not good:
    return False, f"Homs are all bad word types: {joinl(bad,', ')}"

  # for word_type in defs.mw.word_types:
  #   if word_type.word_type in ['abbreviation', 'combining form']:
  #     return False, word_type.word_type

  head_word_ok, reason = False, ''
  hws = []
  for hom in defs.mw.raw:
    word_type = hom.get('fl', '')
    if is_banned(word_type):
      continue

    hw = hom['hwi']['hw']
    hw = hw.replace('*', '')

    if ' ' in hw:
      reason += f'headword:`{hw}` contains space; '
    elif re.match('[A-Z]', hw):
      reason += f'headword:`{hw}` contains uppercase; '
    elif '-' in hw:
      reason += f'headword:`{hw}` contains dash; '
    elif re.search('[^a-z]', hw):
      reason += f'headword:`{hw}` contains non-ascii; '
    elif defs.word != hw and defs.word not in hom['meta']['stems']:
      reason += f"{defs.word} not in HW or stems: {hw}, {hom['meta']['stems']}; "
    elif hom['meta']['offensive']:
      # Don't use a word with any offensive meaning.
      return False, f'`{hw}` is offensive, {hom["shortdef"]}; '
    else:
      hws.append(f'{hw} {hom["shortdef"]}  {hom["meta"]["id"]}')
      # At least one valid headword
      head_word_ok = True
      # print(hw)
      # print(json.dumps(hom, indent=4))
      # print('-------------------------------')
  DEBUG and print(defs.word, 'Headwords:', hws)
  if not head_word_ok:
    return False, reason

  return True, None

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


