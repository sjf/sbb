import re
import elasticsearch
from elasticsearch import Elasticsearch, helpers
import langcodes
from functools import cmp_to_key
from collections import defaultdict
import json
import os
import shlex
from typing import List, Any, Dict, Optional, Tuple
from pyutils.settings import config
from pyutils import *
from model import GSearchResult
from result import Result

class ElasticSearch:
  def __init__(self):
    host = config.get('ELASTIC_HOST')
    api_key = read_value(config.get('ELASTIC_API_KEY_FILE'))
    log(f"Connecting to Elasticsearch {host} api_key={api_key[:4]}...")
    self.es = Elasticsearch(host, api_key = api_key, request_timeout = config.get('ELASTIC_TIMEOUT_SECS'))

    self.page_size = config.get('PAGE_SIZE')
    self.max_page_num = config.get('MAX_PAGE_NUM')
    self.index = config.get('INDEX')
    self.max_retries = config.get('ES_MAX_RETRIES')
    self.retry_delay_secs = config.get('RETRY_DELAY_SECS')

  def upsert_clue(self, url: str, word: str, text: str, date: str) -> None:
    retries = self.max_retries + 1
    success = 0

    doc = {'word': word, 'text': text, 'lastused': date}
    while retries > 0:
      try:
        body = {'doc': doc, 'doc_as_upsert': True}
        self.es.update(index=self.index, id=url, body=body)
        break # Don't retry
      except (elasticsearch.AuthenticationException, elasticsearch.AuthorizationException) as e:
        raise e
      except Exception as ex:
        # Update can fail if e.g. the index is closed because the mappings are being updated.
        log_error(f"Upserting failed with exception:{ex}")
        retries -= 1
        if retries > 0:
          log(f'Retrying... (attempt {self.max_retries + 2 - retries}) after {self.retry_delay_secs} seconds', )
          time.sleep(self.retry_delay_secs)

  def search(self, query) -> Result:
    and_terms = []
    or_terms = [] # Match any of full title, isbn or doi.
    unquoted, quoted = get_quoted_substrings(query.term)
    if unquoted:
      unquoted_t = inexact_phrase('text', self.tokenize(unquoted), 400, 300, 50, 0)
      if not quoted:
        or_terms.append(unquoted_t)
    if quoted:
      quoted_ts = [exact_phrase('text', q, 500) for q in quoted]
      if unquoted:
        # Include the unquoted phrase in the `and` clause
        quoted_ts.append(unquoted_t)
      # All quoted strings must be present.
      or_terms.append(es_and(quoted_ts))
    and_terms.append(es_or(or_terms))

    os.environ.get('DEBUG','') and print(query) # ssss
    es_query = es_and(and_terms)
    hits, has_next = self._search(es_query, query.page_num - 1) # pages start at 1.
    results = mapl(to_clue, hits)
    result = Result(query, results, has_next)
    os.environ.get('DEBUG','') and (print(result)) # ssss
    return result

  def _search(self, es_query, page_num) -> Tuple[List[GSearchResult], bool]:
    body = {
      "query": es_query,
      "from": page_num * self.page_size,
      "size": self.page_size + 1
    }
    # os.environ.get('DEBUG','') and (print(self.index), print(json.dumps(body,indent=2))) # ssss
    search_response = self.es.search(index=self.index, body=body)
    # os.environ.get('DEBUG','') and pprint.pprint(search_response) # ssss
    hits = search_response['hits']['hits'][:self.page_size]
    has_next = len(search_response['hits']['hits']) > self.page_size and (page_num +1) < self.max_page_num
    return (hits, has_next)

  def tokenize(self, s):
    if not s:
      return []
    # Split `s` using the search_analyser.
    body = {'analyzer': 'search_analyser', 'text': s}
    response = self.es.indices.analyze(index=self.index, body=body)
    return [token['token'] for token in response['tokens']]

def to_clue(hit: Dict) -> GSearchResult:
  url = hit['_id']
  word = hit['_source']['word']
  text = hit['_source']['text']
  lastused = hit['_source']['lastused']
  return GSearchResult(url=url, word=word, text=text, lastused=lastused)

def split_quotes(s):
  lex = shlex.shlex(s)
  lex.quotes = '"'
  lex.whitespace_split = True
  lex.commenters = ''
  return list(lex)

def get_quoted_substrings(s):
  # Split s into unquoted search terms and quoted terms.
  # Returns the unquoted terms and a list of quoted terms.
  # The quoted terms will _not retain the enclosing quotes.
  try:
    parts = split_quotes(s)
  except ValueError:
    # Unclosed quote
    try:
      parts = split_quotes(s + '"')
    except:
      return [s],[] # Couldn't parse query.

  quoted, unquoted = [], []
  for p in parts:
    if not p:
      continue # no empty strings
    if p[0] == '"' and p[-1] == '"':
      if len(p) > 2: # no empty quoted strings.
        quoted.append(p[1:-1]) # remove quotes.
    else:
      unquoted.append(p)
  unquoted = joinl(unquoted, ' ', empty='')
  return unquoted, quoted

# Sort by whether ISBN is present. (field is not indexed)
# {
#   "_script": {
#     "type": "number",
#     "script": {
#       "source": f"""
#         if (doc['IdentifierWODash'].value != '') {{
#           return 0;
#         }} else {{
#           return 1;
#         }}
#       """,
#       # "order": "desc"
#     }
#   }
# },

# Document contains the _exact_ search query.
# The terms maybe moved by `slop` positions, they will be scored lower however.
# Slop can fix the author first/last name ordering problem, but it is not ideal
# because they will be scored lower for being re-ordered.
# match_phrase does not support fuzziness.
def exact_phrase(field, s, boost=1, slop=0):
  return {
     "match_phrase": {
        field: {
          "query": s,
          "slop": slop,
          "boost": boost
        }
      }
    }

# Document contains all the terms in `parts`.
# Terms can be slop=5 words away and still be loosely scored as in order.
# Results in order will score higher.
# Spell correction (fuzz) is applied.
def inexact_phrase(field, parts, boost_in_order_nofuzz, boost_out_of_order_nofuzz,
  boost_in_order, boost_out_of_order):
  # Match each term without spelling correction (fuzz).
  nofuzzy_clauses = [
    {
      "span_multi": {
        "match": {
          "fuzzy": {
            field: {
              "value": part,
              "fuzziness": 0
            }
          }
        }
      }
    } for part in parts]
  # Match each term with spelling correction (fuzz).
  fuzzy_clauses = [
    {
      "span_multi": {
        "match": {
          "fuzzy": {
            field: {
              "value": part,
              "fuzziness": "AUTO"
            }
          }
        }
      }
    } for part in parts]
  return es_or(
    [
      # Match the terms _in order_ with slop=5s. No fuzz.
      # Slop can help fix author first/last name order.
      {
        "span_near": {
            "clauses": nofuzzy_clauses,
            "slop": 5,
            "in_order": True,
            "boost": boost_in_order_nofuzz
        }
      },
      # Match the terms in _any order_ (but still close to each other) with slop=5.
      {
        "span_near": {
            "clauses": nofuzzy_clauses,
            "slop": 5,
            "in_order": False,
            "boost": boost_out_of_order_nofuzz
        }
      },
      # Same as above two, but with fuzziness.
      # Fuzzy matches need to be heavily penalized (boosted less)
      # otherwise fuzzy matches that are infrequent words will score
      # higher than exact matches.
      {
        "span_near": {
            "clauses": fuzzy_clauses,
            "slop": 5,
            "in_order": True,
            "boost": boost_in_order
        }
      },
      {
        "span_near": {
            "clauses": fuzzy_clauses,
            "slop": 5,
            "in_order": False,
            "boost": boost_out_of_order
        }
      },
    ])

# Field contains all the words in `s`.
# Up to `percentage_match` words maybe missing.
# The order of words is completely irrelevant.
# Spell checking (fuzz) maybe on or off. Bad spelling does not
# affect scoring.
# Documents with more occurrences of the term(s) will score higher, with no
# regard to matching the order of the query- which is not desireable.
def contains_words(field, s, percentage_match=100, fuzzy=False):
  fuzziness = 'AUTO' if fuzzy else 0
  return {
    "match": {
      field: {
        "query": s,
        "operator": "or",
        "minimum_should_match": f"{percentage_match}%",
        "fuzziness": fuzziness,
      }
    }
  }

# Field contains the _exact string_ `s`.
# Search query is not analyzed, punctuation is not removed etc.
def exact_string(field, s):
  return {"term": {field: s}}

# Field contains any of the _exact strings_ `s`.
# Search query is not analyzed, punctuation is not removed etc.
def any_exact_string(field, l):
  return {"terms": {field: l}}

def es_and(clauses, filters=None):
  result = {"bool":{"must": clauses}} # must means 'and'
  if filters:
    result["bool"]["filter"] = filters
  return result

def es_or(clauses):
  return {"bool":{"should": clauses}} # should means 'or'





