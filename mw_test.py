#!/usr/bin/env python3
import pytest
from testdata import *
from pyutils import *
from model import *
import mw

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

  mw.parse_mw(inputt)

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

  mw.parse_mw(inputt)

  assert inputt == expected

@pytest.mark.parametrize('input_str, expected', [
  ('{bc}a sour substance', 'A sour substance'),
  ('Middle English {it}foul{/it}, from Old English {inf}fugel{/inf};', 'Middle English foul, from Old English <sub>fugel</sub>;'),
  ('domesticated {dx_def}see {dxt|domesticate:1||2}{/dx_def} or wild {d_link|gallinaceous|gallinaceous}birds {dx}compare {dxt|guinea fowl||}, {dxt|jungle fowl||}{/dx}',
   'Domesticated see domesticate or wild gallinaceousbirds compare guinea fowl, jungle fowl')
])
def test_format_mw(input_str, expected):
  assert mw.format_mw(input_str) == expected
