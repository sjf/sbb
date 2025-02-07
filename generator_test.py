#!/usr/bin/env python3
import os
import pytest
import json
import db
from generator import *

@pytest.mark.parametrize('input_str, expected', [
  ('dog', 'd'),
  ('DOG', 'd'),
  ('"DOG"', 'd'),
  ('“ DOG ”', 'd'),
  ('\'dog ', 'd'),
  ('dog 💎', 'd'),
  ('123', '0-9'),
  ('\'dog ', 'd'),
  ('𝘊𝘰𝘶𝘯𝘵 𝘶𝘱 some 𝙖𝙣𝙠𝙡𝙚 𝙗𝙤𝙣𝙚𝙨', 'c'),
  ('Учебное пособие', 'symbols'),
  ('Île Esthétisme', 'i'),
  ('👁🦷', 'symbols'),
])
def test_get_clue_archive_prefix(input_str, expected):
  assert Generator.get_clue_archive_prefix(input_str) == expected
