#!/usr/bin/env python3
import pytest
from pyutils import *
from model import *
from mw import *

def test_dictapis_to_def_wiktionary():
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

  parse_dict_entry(inputt)

  assert inputt == expected

def test_dictapis_to_def_mw():
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

  parse_dict_entry(inputt)

  assert inputt == expected

def test_dictapis_to_def_mw_uns():
  inputt = GDefinition(word="lima",
    retrieved_from = MW_SOURCE,
    retrieved_on = '2025-10-10',
    raw = json.loads(MW_INPUT_2))
  expected = GDefinition(word="lima",
    retrieved_from = MW_SOURCE,
    retrieved_on = '2025-10-10',
    raw = json.loads(MW_INPUT_2),
    source_url = "https://www.merriam-webster.com/dictionary/lima",
    word_types=[
      GWordTypeDefinition(word_type='communications code word', meanings=[
        GWordMeaning(meaning='Used as a code word for the letter l', example=None)]),
      GWordTypeDefinition(word_type='geographical name', meanings=[
        GWordMeaning(meaning='City south-southwest of Toledo in northwestern Ohio population 38,771', example=None),
        GWordMeaning(meaning='City on the Rímac River and capital of Peru population 8,039,000', example=None)]),
      GWordTypeDefinition(word_type='noun', meanings=[
        GWordMeaning(meaning='A bushy or vining tropical American bean (Phaseolus lunatus synonym Phaseolus limensis) that is widely cultivated for its flat edible starchy seed which is usually pale green when immature and whitish or beige when mature', example=None),
        GWordMeaning(meaning='The seed of a lima bean eaten usually cooked as a vegetable see butter bean, sieva bean', example=None)]),
      GWordTypeDefinition(word_type='biographical name', meanings=[
        GWordMeaning(meaning='De 1803–1880 Luiz Alves de Lima e Silva Brazilian general and statesman', example=None)])
      ])

  parse_dict_entry(inputt)

  assert inputt == expected

def test_dictapis_to_def_unsupported():
  inputt = GDefinition(word="lima",
    retrieved_from = 'foo-bar.com/something/lima',
    retrieved_on = '2025-10-10',
    raw = json.loads(MW_INPUT_2))

  with pytest.raises(Exception):
    parse_dict_entry(inputt)

@pytest.mark.parametrize('input_str, expected', [
  ('{bc}a sour substance', 'A sour substance'),
  ('Middle English {it}foul{/it}, from Old English {inf}fugel{/inf};', 'Middle English foul, from Old English <sub>fugel</sub>;'),
  ('domesticated {dx_def}see {dxt|domesticate:1||2}{/dx_def} or wild {d_link|gallinaceous|gallinaceous}birds {dx}compare {dxt|guinea fowl||}, {dxt|jungle fowl||}{/dx}',
   'Domesticated see domesticate or wild gallinaceousbirds compare guinea fowl, jungle fowl')
])
def test_format_mw(input_str, expected):
  assert format_mw(input_str) == expected

WIKTIONARY_SOURCE = 'https://api.dictionaryapi.dev/api/v2/entries/en/tractor'
WIKTIONARY_INPUT = """
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

MW_WORD = "acid"
MW_SOURCE = 'https://dictionaryapi.com/api/v3/references/collegiate/json/acid?key=XXXXXX'
MW_INPUT="""
[
  {
    "meta": {
      "id": "acid:1",
      "uuid": "be36a314-75cd-4209-86fd-03e74d23c197",
      "sort": "010555000",
      "src": "collegiate",
      "section": "alpha",
      "stems": [
        "acid",
        "acids",
        "acidy"
      ],
      "offensive": false
    },
    "hom": 1,
    "hwi": {
      "hw": "acid",
      "prs": [
        {
          "mw": "ˈa-səd",
          "sound": {
            "audio": "acid0001",
            "ref": "c",
            "stat": "1"
          }
        }
      ]
    },
    "fl": "noun",
    "def": [
      {
        "sseq": [
          [
            [
              "sense",
              {
                "sn": "1",
                "dt": [
                  [
                    "text",
                    "{bc}a sour substance"
                  ]
                ],
                "sdsense": {
                  "sd": "specifically",
                  "dt": [
                    [
                      "text",
                      "{bc}any of various typically water-soluble and sour compounds that in solution are capable of reacting with a base {dx_def}see {dxt|base:1||6a}{/dx_def} to form a salt, redden {d_link|litmus|litmus}, and have a {d_link|pH|pH} less than 7, that are hydrogen-containing molecules or ions able to give up a {d_link|proton|proton} to a base, or that are substances able to accept an unshared pair of electrons from a base"
                    ]
                  ]
                }
              }
            ]
          ],
          [
            [
              "sense",
              {
                "sn": "2",
                "dt": [
                  [
                    "text",
                    "{bc}something incisive, biting, or {d_link|sarcastic|sarcastic} "
                  ],
                  [
                    "vis",
                    [
                      {
                        "t": "a social satire dripping with {wi}acid{/wi}"
                      }
                    ]
                  ]
                ]
              }
            ]
          ],
          [
            [
              "sense",
              {
                "sn": "3",
                "dt": [
                  [
                    "text",
                    "{bc}{sx|lsd||}"
                  ]
                ]
              }
            ]
          ]
        ]
      }
    ],
    "uros": [
      {
        "ure": "ac*idy",
        "prs": [
          {
            "mw": "ˈa-sə-dē"
          }
        ],
        "fl": "adjective"
      }
    ],
    "et": [
      [
        "text",
        "borrowed from Medieval Latin {it}acidum,{/it} going back to Latin, neuter of {it}acidus{/it} {et_link|acid:2|acid:2}"
      ]
    ],
    "date": "1650{ds||1||}",
    "shortdef": [
      "a sour substance; specifically : any of various typically water-soluble and sour compounds that in solution are capable of reacting with a base to form a salt, redden litmus, and have a pH less than 7, that are hydrogen-containing molecules or ions able to give up a proton to a base, or that are substances able to accept an unshared pair of electrons from a base",
      "something incisive, biting, or sarcastic",
      "lsd"
    ]
  }
]
"""
MW_WORD_2 = "lima"
MW_SOURCE_2 = 'https://dictionaryapi.com/api/v3/references/collegiate/json/lima?key=96fd70b1-b580-4119-b2ce-25e0988a2252'
MW_INPUT_2 = """
[
  {
    "meta": {
      "id": "Lima",
      "uuid": "8d2f2f09-ab01-48f3-92b0-4efccd5350d6",
      "sort": "120165000",
      "src": "collegiate",
      "section": "alpha",
      "stems": [
        "Lima"
      ],
      "offensive": false
    },
    "hwi": {
      "hw": "Li*ma",
      "prs": [
        {
          "mw": "ˈlē-mə",
          "sound": {
            "audio": "lima0001",
            "ref": "c",
            "stat": "1"
          }
        }
      ]
    },
    "fl": "communications code word",
    "def": [
      {
        "sseq": [
          [
            [
              "sense",
              {
                "dt": [
                  [
                    "uns",
                    [
                      [
                        [
                          "text",
                          "used as a code word for the letter {it}l{/it}"
                        ]
                      ]
                    ]
                  ]
                ]
              }
            ]
          ]
        ]
      }
    ],
    "date": "1952",
    "shortdef": [
      "—used as a code word for the letter l"
    ]
  },
  {
    "meta": {
      "id": "Lima:g",
      "uuid": "2e4a7363-e558-48c1-8193-b6f73b5425f2",
      "sort": "280028000",
      "src": "collegiate",
      "section": "geog",
      "stems": [
        "Lima"
      ],
      "offensive": false
    },
    "hwi": {
      "hw": "Li*ma"
    },
    "fl": "geographical name",
    "def": [
      {
        "sseq": [
          [
            [
              "sense",
              {
                "sn": "1",
                "prs": [
                  {
                    "mw": "ˈlī-mə",
                    "sound": {
                      "audio": "gglim01v",
                      "ref": "c",
                      "stat": "1"
                    }
                  }
                ],
                "dt": [
                  [
                    "text",
                    "city south-southwest of Toledo in northwestern Ohio {it}population{/it} 38,771"
                  ]
                ]
              }
            ]
          ],
          [
            [
              "sense",
              {
                "sn": "2",
                "prs": [
                  {
                    "mw": "ˈlē-mə",
                    "sound": {
                      "audio": "lima0001",
                      "ref": "c",
                      "stat": "1"
                    }
                  }
                ],
                "dt": [
                  [
                    "text",
                    "city on the Rímac River and capital of Peru {it}population{/it} 8,039,000"
                  ]
                ]
              }
            ]
          ]
        ]
      }
    ],
    "shortdef": [
      "city south-southwest of Toledo in northwestern Ohio population 38,771",
      "city on the Rímac River and capital of Peru population 8,039,000"
    ]
  },
  {
    "meta": {
      "id": "lima bean",
      "uuid": "3f5a7f3a-7802-411d-b2fc-58ef879929fb",
      "sort": "120165100",
      "src": "collegiate",
      "section": "alpha",
      "stems": [
        "lima bean",
        "lima beans"
      ],
      "offensive": false
    },
    "hwi": {
      "hw": "li*ma bean",
      "prs": [
        {
          "mw": "ˈlī-mə-",
          "sound": {
            "audio": "limabe01",
            "ref": "c",
            "stat": "1"
          }
        }
      ]
    },
    "fl": "noun",
    "def": [
      {
        "sseq": [
          [
            [
              "sense",
              {
                "sn": "1",
                "dt": [
                  [
                    "text",
                    "{bc}a bushy or vining tropical American bean ({it}Phaseolus lunatus{/it} synonym {it}Phaseolus limensis{/it}) that is widely cultivated for its flat edible starchy seed which is usually pale green when immature and whitish or beige when mature"
                  ]
                ]
              }
            ]
          ],
          [
            [
              "sense",
              {
                "sn": "2",
                "dt": [
                  [
                    "text",
                    "{bc}the seed of a lima bean eaten usually cooked as a vegetable {dx}see {dxt|butter bean||}, {dxt|sieva bean||}{/dx}"
                  ]
                ]
              }
            ]
          ]
        ]
      }
    ],
    "et": [
      [
        "text",
        "{it}Lima{/it}, Peru"
      ]
    ],
    "date": "1756{ds||1||}",
    "shortdef": [
      "a bushy or vining tropical American bean (Phaseolus lunatus synonym Phaseolus limensis) that is widely cultivated for its flat edible starchy seed which is usually pale green when immature and whitish or beige when mature",
      "the seed of a lima bean eaten usually cooked as a vegetable"
    ]
  },
  {
    "meta": {
      "id": "Caxias:b",
      "uuid": "3337c2ae-8836-467d-96ae-aee172b4284d",
      "sort": "301028000",
      "src": "collegiate",
      "section": "biog",
      "stems": [
        "Caxias",
        "Duque Caxias",
        "Luiz Alves de Lima e Silva",
        "Luiz Alves de Lima e Silva, Duke of Caxias",
        "Luiz Alves de Lima e Silva, Duque de Caxias"
      ],
      "offensive": false
    },
    "hwi": {
      "hw": "Ca*xi*as",
      "prs": [
        {
          "mw": "kə-ˈshē-əs",
          "sound": {
            "audio": "bixcax01",
            "ref": "c",
            "stat": "1"
          }
        }
      ]
    },
    "fl": "biographical name",
    "def": [
      {
        "sseq": [
          [
            [
              "sense",
              {
                "dt": [
                  [
                    "bnw",
                    {
                      "pname": "Du*que",
                      "prs": [
                        {
                          "mw": "ˈdü-kə",
                          "sound": {
                            "audio": "bixcax02",
                            "ref": "c",
                            "stat": "1"
                          }
                        }
                      ]
                    }
                  ],
                  [
                    "text",
                    " de 1803–1880 {it}Luiz Alves de Lima e Silva{/it} Brazilian general and statesman"
                  ]
                ]
              }
            ]
          ]
        ]
      }
    ],
    "shortdef": [
      "Duque de 1803—1880 Luiz Alves de Lima e Silva Brazilian general and statesman"
    ]
  }
]
"""
