#!/usr/bin/env python3
import mw
from typing import List, Any, Dict, Optional, Set
from pyutils import *
from pyutils.settings import config
from model import *
from requester import *

WIKTIONARY_API = 'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
MW_API = 'https://dictionaryapi.com/api/v3/references/collegiate/json/{word}?key=96fd70b1-b580-4119-b2ce-25e0988a2252'
DICT_APIS = [MW_API, WIKTIONARY_API]

class Dicts:
  def __init__(self):
    self.requester = Requester(sleep=0.5)

  def lookup(self, words: List[str]) -> List[GDefinitions]:
    if not words: return []
    words = slist(uniq(words))

    n = 0
    results, missing = [], []
    log(f"Looking up [{len(words)}] words:\n{joinl(words, ', ')}")
    for word in words:
      defs = [self._retrieve_from_dict_api(word, url_fmt) for url_fmt in DICT_APIS]
      result = GDefinitions(word=word, defs=defs)
      if result.has_def:
        n += 1
      else:
        missing.append(word)
      results.append(result)
    mesg = f", could not find {len(missing)}: {joinl(missing, sep=', ')}" if missing else ''
    log(f"Got definitions for {n} words{mesg}.")
    return results

  @staticmethod
  def _parse_dict_entry(deff: GDefinition) -> None:
    fromm = deff.retrieved_from
    if "api.dictionaryapi.dev" in fromm:
      Dicts._parse_wiktionary(deff)
    elif "dictionaryapi.com" in fromm:
      mw.parse_mw(deff)
    else:
      raise Exception(f"Unhandled dict source {fromm}")

  @staticmethod
  def _parse_wiktionary(deff: GDefinition) -> None:
    # Wikitionary 3rd party API.
    deff.source_url = deff.raw[0]['sourceUrls'][0] # idk why there needs to be >1 source url.
    for sense in deff.raw:
      for m in sense.get('meanings',[]):
        td = GWordTypeDefinition(word_type = m['partOfSpeech'])
        deff.word_types.append(td)
        for d in m['definitions']:
          td.meanings.append(GWordMeaning(meaning = d['definition'], example = d.get('example',None)))

  def _retrieve_from_dict_api(self, word: str, url_fmt: str) -> GDefinition:
    url = url_fmt.format(word=word)
    response = self.requester.get(url)
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    raw = response.json() if response else []
    result = GDefinition(word=word, retrieved_on=date, retrieved_from=url, raw=raw)
    if not response:
      return result
    if isinstance(response.json(), list) and all(isinstance(item, str) for item in response.json()):
      # MW never returns 404, it returns a list of suggested words.
      return result
    Dicts._parse_dict_entry(result)
    return result
