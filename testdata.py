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

ES_UPDATES_1 = [
  call(index='sbb', id=P1_URL, body={'doc': {'type': 'puzzle', 'url': P1_URL, 'date': D1, 'letters': 'DEFOTUX',
    'center_letter': 'D', 'outer_letters': 'TEFOUX', 'month_day': 'december 24', 'day_month': '24 december',
    'month_day_year': 'december 24 2024', 'day_month_year': '24 december 2024'}, 'doc_as_upsert': True}),
  call(index='sbb', id='14d2e7bdf4e638d84f3cc9487b21653b',
     body={'doc': {'type': 'clue', 'url': U1_A, 'date': D1, 'word': W1_A, 'text': T1_A}, 'doc_as_upsert': True}),
  call(index='sbb', id='4423ba5567a73d032a44020d7113fc6e',
     body={'doc': {'type': 'clue', 'url': U1_C, 'date': D1, 'word': W1_C, 'text': T1_C}, 'doc_as_upsert': True}),
  call(index='sbb', id='fb947212e7c9146f5976fcd3006ad790',
     body={'doc': {'type': 'clue', 'url': U1_B, 'date': D1, 'word': W1_B, 'text': T1_B}, 'doc_as_upsert': True}),
]
ES_UPDATES_2 = [
  call(index='sbb', id=P2_URL, body={'doc': {'type': 'puzzle', 'url': P2_URL, 'date': D2,
    'letters': 'BGILMOR', 'center_letter': 'L', 'outer_letters': 'BGIMOR',
    'month_day': 'december 29', 'day_month': '29 december', 'month_day_year': 'december 29 2024',
    'day_month_year': '29 december 2024'}, 'doc_as_upsert': True}),
  call(index='sbb', id='25fe9a0a72d490a43911e3f5188ddcc8',
    body={'doc': {'type': 'clue', 'url': U2_A, 'date': D2, 'word': W2_A, 'text': T2_A}, 'doc_as_upsert': True}),
  call(index='sbb', id='38a31778a5401e9e9d3911d62fa317eb',
     body={'doc': {'type': 'clue', 'url': U2_C, 'date': D2, 'word': W2_C, 'text': T2_C}, 'doc_as_upsert': True}),
  call(index='sbb', id='fe9d98a72c3099f133a1115f85b0d1e3',
     body={'doc': {'type': 'clue', 'url': U2_B, 'date': D2, 'word': W2_B, 'text': T2_B}, 'doc_as_upsert': True}),
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

