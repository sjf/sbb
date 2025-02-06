#!/usr/bin/env python3
import pytest
from pyutils import *
from model import *

def test_dictapis_to_def_dictionarydotcom():
  expected = GDefinition(word="tractor",
    source_url = "https://en.wiktionary.org/wiki/tractor",
    source = 'wiktionary.org',
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

  assert dictapis_to_def(DICT_INPUT, DICT_SOURCE) == expected

def test_dictapis_to_def_unsupported():
  assert dictapis_to_def(DICT_SOURCE, "https://something.else/foo/bar") == None

DICT_SOURCE = 'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
DICT_INPUT = """
[
  {
    "word": "tractor",
    "phonetic": "/ˈtɹæktə/",
    "phonetics": [
      {
        "text": "/ˈtɹæktə/",
        "audio": ""
      },
      {
        "text": "/ˈtɹæktɚ/",
        "audio": "https://api.dictionaryapi.dev/media/pronunciations/en/tractor-us.mp3",
        "sourceUrl": "https://commons.wikimedia.org/w/index.php?curid=592084",
        "license": {
          "name": "BY-SA 3.0",
          "url": "https://creativecommons.org/licenses/by-sa/3.0"
        }
      }
    ],
    "meanings": [
      {
        "partOfSpeech": "noun",
        "definitions": [
          {
            "definition": "A vehicle used in farms e.g. for pulling farm equipment and preparing the fields.",
            "example": "The tractor pulled the trailer",
            "synonyms": [],
            "antonyms": []
          },
          {
            "definition": "A truck (or lorry) for pulling a semi-trailer or trailer.",
            "synonyms": [],
            "antonyms": []
          },
          {
            "definition": "Any piece of machinery that pulls something.",
            "synonyms": [],
            "antonyms": []
          },
          {
            "definition": "An airplane where the propeller is located in front of the fuselage",
            "synonyms": [],
            "antonyms": []
          },
          {
            "definition": "(rail transportation) A British Rail Class 37 locomotive.",
            "synonyms": [],
            "antonyms": []
          },
          {
            "definition": "A metal rod used in tractoration, or Perkinism.",
            "synonyms": [],
            "antonyms": []
          }
        ],
        "synonyms": [],
        "antonyms": []
      },
      {
        "partOfSpeech": "verb",
        "definitions": [
          {
            "definition": "To prepare (land) with a tractor.",
            "synonyms": [],
            "antonyms": []
          },
          {
            "definition": "To move with a tractor beam.",
            "synonyms": [],
            "antonyms": []
          },
          {
            "definition": "To treat by means of tractoration, or Perkinism.",
            "synonyms": [],
            "antonyms": []
          }
        ],
        "synonyms": [],
        "antonyms": []
      }
    ],
    "license": {
      "name": "CC BY-SA 3.0",
      "url": "https://creativecommons.org/licenses/by-sa/3.0"
    },
    "sourceUrls": [
      "https://en.wiktionary.org/wiki/tractor"
    ]
  }
]
"""
