#!/usr/bin/env python3
import pytest
from testdata import *
from pyutils import *
from model import *
from dicts import *

def test__parse_dict_entry_wiktionary():
  inputt = GDefinition(word="tractor",
    retrieved_from = WIKTIONARY_SOURCE,
    retrieved_on = '2025-10-10',
    raw = json.loads(WIKTIONARY_INPUT))
  expected = GDefinition(word="tractor",
    retrieved_from = WIKTIONARY_SOURCE,
    retrieved_on = '2025-10-10',
    raw = json.loads(WIKTIONARY_INPUT),
    source_url = "https://en.wiktionary.org/wiki/tractor",
    word_types=[
      GWordTypeDefinition(word_type="noun",
        meanings=[
          GWordMeaning(meaning="A vehicle used in farms e.g. for pulling farm equipment and preparing the fields.",
            example="The tractor pulled the trailer"),
          GWordMeaning(meaning="A truck (or lorry) for pulling a semi-trailer or trailer."),
          GWordMeaning(meaning="Any piece of machinery that pulls something."),
          GWordMeaning(meaning="An airplane where the propeller is located in front of the fuselage"),
          GWordMeaning(meaning="(rail transportation) A British Rail Class 37 locomotive."),
          GWordMeaning(meaning="A metal rod used in tractoration, or Perkinism."),
        ]),
      GWordTypeDefinition(word_type="verb",
        meanings=[
          GWordMeaning(meaning="To prepare (land) with a tractor."),
          GWordMeaning(meaning="To move with a tractor beam."),
          GWordMeaning(meaning="To treat by means of tractoration, or Perkinism."),
        ])
    ])

  Dicts._parse_dict_entry(inputt)

  assert inputt == expected

def test__parse_dict_entry_mw():
  inputt = GDefinition(word="acid",
    retrieved_from = MW_SOURCE,
    retrieved_on = '2025-10-10',
    raw = json.loads(MW_INPUT))
  expected = GDefinition(word="acid",
    retrieved_from = MW_SOURCE,
    retrieved_on = '2025-10-10',
    raw = json.loads(MW_INPUT),
    source_url = "https://www.merriam-webster.com/dictionary/acid",
    word_types=[
      GWordTypeDefinition(word_type='noun',
        meanings=[
          GWordMeaning(meaning='A sour substance', example=None),
          GWordMeaning(meaning='Something incisive, biting, or sarcastic', example='a social satire dripping with acid'),
          GWordMeaning(meaning='Lsd', example=None)
        ])
      ])

  Dicts._parse_dict_entry(inputt)

  assert inputt == expected


def test__parse_dict_entry__unsupported():
  inputt = GDefinition(word="lima",
    retrieved_from = 'foo-bar.com/something/lima',
    retrieved_on = '2025-10-10',
    raw = json.loads(MW_INPUT_2))

  with pytest.raises(Exception):
      Dicts._parse_dict_entry(inputt)
