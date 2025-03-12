import re
import elasticsearch
from elasticsearch import Elasticsearch, helpers
import langcodes
from functools import cmp_to_key
from collections import defaultdict
import datetime as dtt

import json
import os
import shlex
from typing import List, Any, Dict, Optional, Tuple
from pyutils.settings import config
from pyutils import *
from model import GSearchResult, GClueSearchResult, GPuzzleSearchResult
from query import Query
from site_util import url_for
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

  def upsert_puzzle(self, date: str, center_letter: str, outer_letters: str) -> None:
    letters = joinl(sorted(outer_letters + center_letter), sep='')
    dt = datetime.datetime.strptime(date, '%Y-%m-%d')
    month_day =      normalize(dt.strftime('%B %-d'))
    month_day_year = normalize(dt.strftime('%B %-d %Y'))
    day_month =      normalize(dt.strftime('%-d %B'))
    day_month_year = normalize(dt.strftime('%-d %B %Y'))
    url = url_for(date)
    doc = {'type': 'puzzle', 'url': url, 'date': date,
            'letters': letters, 'center_letter': center_letter, 'outer_letters': outer_letters,
            'month_day': month_day, 'day_month': day_month,
            'month_day_year': month_day_year, 'day_month_year': day_month_year}
    id_ = url
    self._upsert(doc, id_)

  def upsert_clue(self, url: str, word: str, text: str, date: str) -> None:
    # If the clues are inserted in chronological order, only the last clue will be stored when there
    # are clues with the same text and word. We only the most recent to show up in the search results.
    doc = {'type': 'clue', 'url': url, 'date': date, 'word': word, 'text': text}
    id_ = md5_value(word + '_' + text)
    self._upsert(doc, id_)

  def _upsert(self, doc: Dict[Any,Any], id_: str) -> None:
    retries = self.max_retries + 1
    success = 0

    while retries > 0:
      try:
        body = {'doc': doc, 'doc_as_upsert': True}
        self.es.update(index=self.index, id=id_, body=body)
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

  def search(self, query: Query) -> Result:
    q = query.term
    es_query = es_or([self.search_clues(q), self.search_puzzles(q)])

    config.get('DEBUG') and print(json.dumps(es_query)) # ssss
    hits, has_next = self._search(es_query, query.page_num - 1) # pages start at 1 in the query.
    config.get('DEBUG') and print(joinl(hits)) # ssss

    results = mapl(to_search_result, hits)
    results = sorted(results)
    result = Result(query, results, has_next)
    config.get('DEBUG') and (print(result)) # ssss

    return result

  def search_clues(self, query) -> Dict[str, Any]:
    and_terms = [exact_string('type', 'clue')]
    or_terms = []
    unquoted, quoted = get_quoted_substrings(query)
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
    es_query = es_and(and_terms)
    return es_query

  def search_puzzles(self, q: str) -> Dict[str, Any]:
    q = normalize(q)
    or_terms = [exact_string('month_day', q),
                 exact_string('month_day_year', q),
                 exact_string('day_month', q),
                 exact_string('day_month_year', q)]
    l = q.replace(' ', '').upper()
    l = joinl(sorted(l), sep='')
    if len(l) == len(set(l)) == 7: # and 's' not in l:
      or_terms.append(exact_string('letters', l))

    return es_and([exact_string('type', 'puzzle'), es_or(or_terms)])

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

def to_search_result(hit: Dict) -> GSearchResult:
  clue, puzzle = None, None
  score = hit['_score']
  url = hit['_source']['url']
  date = hit['_source']['date']

  if hit['_source']['type'] == 'clue':
    word = hit['_source']['word']
    text = hit['_source']['text']
    clue = GClueSearchResult(word=word, text=text)
  else:
    center_letter = hit['_source']['center_letter']
    outer_letters = list(hit['_source']['outer_letters'])
    puzzle = GPuzzleSearchResult(center_letter=center_letter, outer_letters=outer_letters)

  return GSearchResult(score=score, date=date, url=url, clue=clue, puzzle=puzzle)

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


