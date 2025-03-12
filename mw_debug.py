#!/usr/bin/env python3
import sys
import json
from typing import List, Any, Dict, Optional, Set
from pyutils import *
from pyutils.settings import config
import mw
from dicts import Dicts
from model import *
from requester import *

class MwDebug:
  def __init__(self):
    self.requester = Requester(sleep=0.5)
    self.dicts = Dicts()

  def check_good(self, words: List[str]) -> None:
    defs = self.dicts.lookup(words)
    for deff in defs:
      if deff.mw:
        print(json.dumps(deff.mw.raw, indent=4))
      is_good, reason = mw.is_good(deff)
      print(f'{deff.word}: good:{is_good} {reason}')

if __name__ == '__main__':
  mwd = MwDebug()
  if len(sys.argv) == 1:
    log_fatal(f'Usage: {sys.argv[0]} words...')
  if len(sys.argv) > 1:
    mwd.check_good(sys.argv[1:])
