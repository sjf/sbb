#!/usr/bin/env python3
from dataclasses import dataclass, asdict, fields, field
from typing import List, Any, Dict, Optional
from pyutils import *
from pyutils.settings import config
from model import *
import mw

class Wordlist:
  def __init__(self):
    # Loads these in this order.
    self.allow_list = self.load_allowlist()
    # Load the denylist minus the allowlist.
    self.deny_list = self.load_denylist()
    # Load the wordlist minus the denylist.
    self.all_words = self.load_wordlist()

  def filter_bad(self, words: List[str]) -> List[str]:
    result = []
    for word in words:
      if word in self.deny_list:
        continue
      result.append(word)
    return sorted(result)

  def load_allowlist(self) -> set[str]:
    lines = read_lines(config['ALLOWLIST'])
    return set(lines)

  def load_wordlist(self) -> Dict[frozenset[str], List[str]]:
    result = defaultdict(list)
    with open(config['WORDLIST']) as f:
      for word in f:
        word = word.strip()
        if len(word) < 4:
          continue # too short.
        if re.match('[^a-z]', word):
          continue # contains uppercase; punctuation e.g. hyphen, period, apostrophe; or digits.
        if 's' in word:
          continue # letter set will never contain s; this is a choice by the game creator.
        if word in self.deny_list:
          continue # already disallowed.
        word = word.lower()
        ws = frozenset(word)
        result[ws].append(word)
    return result

  def load_denylist(self) -> Dict[str,str]:
    if not exists(config['DENYLIST']):
      log_error(f"Deny list {config['DENYLIST']} is missing.")
      touch(config['DENYLIST'])

    result = {}
    for filename in [config['DENYLIST'], config['CURATED_DENYLIST']]:
      with open(filename) as fh:
        for line in fh:
          line = line.strip()
          # Format is word:reason, reason is only used as documentation.
          parts = line.split(':', 1)
          word = parts[0]
          if word in self.allow_list:
            continue
          reason = parts[1] if len(parts) > 1 else ''
          result[word] = reason
    return result

  def update_denylist_from_definitions(self, defs: List[GDefinitions]) -> None:
    n_added = 0
    for deff in defs:
      word = deff.word
      if word in self.deny_list:
        continue
      is_good, reason = mw.is_good(deff)
      # log(f"{word}\n{reason} {deff.mw}")
      if is_good:
        continue
      if word in self.allow_list:
        log(f'{word} considered bad by MW because "{reason}", but overriden by allowlist')
        continue
      log(f'Adding {word} to denylist because "{reason}"')
      self.deny_list[word] = reason
      n_added += 1

    if n_added:
      with open(config['DENYLIST'], 'w') as fh:
        for word,reason in sorted(self.deny_list.items()):
          fh.write(f'{word}:{reason}\n')
      log(f"Added {n_added} words to deny list.")

