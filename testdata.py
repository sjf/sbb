from unittest.mock import call
from model import *
from storage import *
from site_util import url_for

##### Test Data for files in test-data/ #####
FILE_1 = 'scraped/puzzle-1.json'
FILE_1_NOCLUES = 'scraped/puzzle-1-early.json'
FILE_2 = 'scraped/puzzle-2.json'
FILE_3 = 'scraped/puzzle-3.json'

D1 = '2024-12-24'
D2 = '2024-12-29'
P1_URL = url_for(D1)
P2_URL = url_for(D2)

C1 = 'D'
C2 = 'L'
L1 = ['T', 'E', 'F', 'O', 'U', 'X']
L2 = ['B', 'G', 'I', 'M', 'O', 'R']
W1_A = 'outfoxed'
W1_B = 'tofu'
W1_C = 'detox'

U1_A = '/clue/defeated-a-woodland-creature'
U1_B = '/clue/soft-hard-or-pressed-soy-bean-curd'
U1_C = '/clue/go-cold-turkey'

T1_A = 'Defeated (a woodland creature)'
T1_B = 'Soft, hard, or pressed soy bean curd'
T1_C = 'Go cold turkey'

W2_A = 'imbroglio'
W2_B = 'olio'
W2_C = 'puzzle-2-word-for-detox'

U2_A = '/clue/an-embarrassing-situation'
U2_B = '/clue/hodge-lodge'
U2_C = '/clue/go-cold-turkey'

T2_A = 'An embarrassing situation'
T2_B = 'Hodge lodge'
T2_C = 'Go cold turkey!!!!!'

ES_UPDATE_P1 = {
  '_op_type': 'index',
  '_index': 'sbb',
  '_id': P1_URL,
  '_source': {
      'type': 'puzzle',
      'url': P1_URL,
      'date': D1,
      'letters': 'DEFOTUX',
      'center_letter': C1,
      'outer_letters': 'TEFOUX',
      'month_day': 'december 24',
      'day_month': '24 december',
      'month_day_year': 'december 24 2024',
      'day_month_year': '24 december 2024',
  },
  'doc_as_upsert': True
}
ES_UPDATES_1 = [
  ES_UPDATE_P1,
  {
    '_op_type': 'index',
    '_index': 'sbb',
    '_id': '14d2e7bdf4e638d84f3cc9487b21653b',
    '_source': {
        'type': 'clue',
        'url': U1_A,
        'date': D1,
        'word': W1_A,
        'text': T1_A
    },
    'doc_as_upsert': True
  },
  {
    '_op_type': 'index',
    '_index': 'sbb',
    '_id': '4423ba5567a73d032a44020d7113fc6e',
    '_source': {
        'type': 'clue',
        'url': U1_C,
        'date': D1,
        'word': W1_C,
        'text': T1_C
    },
    'doc_as_upsert': True
  },
  {
    '_op_type': 'index',
    '_index': 'sbb',
    '_id': 'fb947212e7c9146f5976fcd3006ad790',
    '_source': {
        'type': 'clue',
        'url': U1_B,
        'date': D1,
        'word': W1_B,
        'text': T1_B
    },
    'doc_as_upsert': True
  }]

ES_UPDATES_2 = [
  {
    '_op_type': 'index',
    '_index': 'sbb',
    '_id': P2_URL,
    '_source': {
      'type': 'puzzle',
      'url': P2_URL,
      'date': D2,
      'letters': 'BGILMOR',
      'center_letter': C2,
      'outer_letters': 'BGIMOR',
      'month_day': 'december 29',
      'day_month': '29 december',
      'month_day_year': 'december 29 2024',
      'day_month_year': '29 december 2024',
    },
    'doc_as_upsert': True
  },
{
    '_op_type': 'index',
    '_index': 'sbb',
    '_id': '25fe9a0a72d490a43911e3f5188ddcc8',
    '_source': {
      'type': 'clue',
      'url': U2_A,
      'date': D2,
      'word': W2_A,
      'text': T2_A
    },
    'doc_as_upsert': True
  },
  {
    '_op_type': 'index',
    '_index': 'sbb',
    '_id': '38a31778a5401e9e9d3911d62fa317eb',
    '_source': {
      'type': 'clue',
      'url': U2_C,
      'date': D2,
      'word': W2_C,
      'text': T2_C
    },
    'doc_as_upsert': True
  },
  {
    '_op_type': 'index',
    '_index': 'sbb',
    '_id': 'fe9d98a72c3099f133a1115f85b0d1e3',
    '_source': {
      'type': 'clue',
      'url': U2_B,
      'date': D2,
      'word': W2_B,
      'text': T2_B
    },
    'doc_as_upsert': True
  }
]
ES_UPDATES = ES_UPDATES_1 + ES_UPDATES_2

C1_A = GClueAnswer(word=W1_A, text=T1_A, puzzle_dates=[D1], definitions=GDefinitions(word=W1_A,defs=[]))
C1_B = GClueAnswer(word=W1_B, text=T1_B, puzzle_dates=[D1], definitions=GDefinitions(word=W1_B,defs=[]))
C1_C = GClueAnswer(word=W1_C, text=T1_C, puzzle_dates=[D1], definitions=GDefinitions(word=W1_C,defs=[]))
CS_1 = [C1_A, C1_B, C1_C]

C2_A = GClueAnswer(word=W2_A, text=T2_A, puzzle_dates=[D2], definitions=GDefinitions(word=W2_A,defs=[]))
C2_B = GClueAnswer(word=W2_B, text=T2_B, puzzle_dates=[D2], definitions=GDefinitions(word=W2_B,defs=[]))
C2_C = GClueAnswer(word=W2_C, text=T2_C, puzzle_dates=[D2], definitions=GDefinitions(word=W2_C,defs=[]))
CS_2 = [C2_A, C2_B, C2_C]

GC_PAGES = sorted([
  GCluePage(url=U1_A, _clue_answers=[C1_A]),
  GCluePage(url=U1_B, _clue_answers=[C1_B]),
  GCluePage(url=U1_C, _clue_answers=[C1_C, C2_C]),
  GCluePage(url=U2_A, _clue_answers=[C2_A]),
  GCluePage(url=U2_B, _clue_answers=[C2_B]),
])

A1_A = GAnswer(word=W1_A, is_pangram=True,  text=T1_A, url=U1_A, puzzle_date=D1, definitions=GDefinitions(word=W1_A,defs=[]))
A1_B = GAnswer(word=W1_B, is_pangram=False, text=T1_B, url=U1_B, puzzle_date=D1, definitions=GDefinitions(word=W1_B,defs=[]))
A1_C = GAnswer(word=W1_C, is_pangram=False, text=T1_C, url=U1_C, puzzle_date=D1, definitions=GDefinitions(word=W1_C,defs=[]))
AS_1 = sorted([A1_A, A1_B, A1_C])

A1_NC_A = GAnswer(word=W1_A, is_pangram=True,  text=None, url=None, puzzle_date=D1, definitions=GDefinitions(word=W1_A,defs=[]))
A1_NC_B = GAnswer(word=W1_B, is_pangram=False, text=None, url=None, puzzle_date=D1, definitions=GDefinitions(word=W1_B,defs=[]))
A1_NC_C = GAnswer(word=W1_C, is_pangram=False, text=None, url=None, puzzle_date=D1, definitions=GDefinitions(word=W1_C,defs=[]))
AS_NC_1 = sorted([A1_NC_A, A1_NC_B, A1_NC_C])

A2_A = GAnswer(word=W2_A, is_pangram=True,  text=T2_A, url=U2_A, puzzle_date=D2, definitions=GDefinitions(word=W2_A,defs=[]))
A2_B = GAnswer(word=W2_B, is_pangram=False, text=T2_B, url=U2_B, puzzle_date=D2, definitions=GDefinitions(word=W2_B,defs=[]))
A2_C = GAnswer(word=W2_C, is_pangram=False, text=T2_C, url=U2_C, puzzle_date=D2, definitions=GDefinitions(word=W2_C,defs=[]))
AS_2 = sorted([A2_A, A2_B, A2_C])
AS = sorted(AS_1 + AS_2)

GP_1 = GPuzzle(date=D1, center_letter=C1, outer_letters=L1, _answers=AS_1, hints=[], missing_answers=[])
GP_2 = GPuzzle(date=D2, center_letter=C2, outer_letters=L2, _answers=AS_2, hints=[], missing_answers=[])
GPS = [GP_2, GP_1]

GDEF1_A = GDefinitions(word=W1_A,
  defs=[GDefinition(word=W1_A,
      retrieved_on='2024-01-01',
      retrieved_from='https://dictionaryapi.com/api/v3/references/collegiate/json/outfoxed?key=ABC-123',
      raw={"source-def":"outfoxed-def"},
      source_url='https://merrian-webster.com/dict/outfoxed',
      word_types=[GWordTypeDefinition(word_type='noun', meanings=[])])
  ])

H1_A = Hint(score=10, text='These words have x in the middle.', words=[W1_A, W1_B])
H1_B = Hint(score=9,  text='This word is from Japanese.',       words=[W1_C])
HS_1 = [H1_A, H1_B]

## Storage classes
P_1 = Puzzle(date=D1, center_letter=C1, outer_letters=joinl(L1, sep=''), hints='', missing_answers='[]')
P_2 = Puzzle(date=D2, center_letter=C2, outer_letters=joinl(L2, sep=''), hints='', missing_answers='[]')

CL1_A = Clue(text=T1_A, url=U1_A)
CL1_B = Clue(text=T1_B, url=U1_B)

AN1_A = Answer(word=W1_A, is_pangram=True, puzzle_id=1, clue_id=None)
AN1_B = Answer(word=W1_B, is_pangram=True, puzzle_id=1, clue_id=None)
AN1_C = Answer(word=W1_C, is_pangram=True, puzzle_id=1, clue_id=None)

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
MW_SOURCE_2 = 'https://dictionaryapi.com/api/v3/references/collegiate/json/lima?key=ABCD'
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
