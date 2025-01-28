import re
import elasticsearch
from elasticsearch import Elasticsearch
import langcodes
from functools import cmp_to_key
from collections import defaultdict
import json
import os
import shlex

from mbutils.settings import config
from mbutils import *
from gunicorn_util import *

class ElasticSearch:
  def __init__(self):
    host = config.get('ELASTIC_HOST')
    api_key = read_value(config.get('ELASTIC_API_KEY_FILE'))
    access_log(f"Connecting to Elasticsearch {host}")
    self.es = Elasticsearch(host, api_key = api_key)
    self.page_size = config.get('PAGE_SIZE')
    self.index = config.get('INDEX')

  def search(self, query):
    return [] #sjfsjf
    and_terms = []
    or_terms = [] # Match any of full title, isbn or doi.
    unquoted, quoted = get_quoted_substrings(query.search)
    if unquoted:
      unquoted_t = inexact_phrase('full_title', self.tokenize(unquoted), 400, 300, 50, 0)
      if not quoted:
        or_terms.append(unquoted_t)
    if quoted:
      quoted_ts = [exact_phrase('full_title', q, 500) for q in quoted]
      if unquoted:
        # Include the unquoted phrase in the `and` clause
        quoted_ts.append(unquoted_t)
      # All quoted strings must be present.
      or_terms.append(es_and(quoted_ts))
    and_terms.append(es_or(or_terms))

    filters = get_filters(query)
    sort = get_sort(query)

    os.environ.get('DEBUG','') and print(query) # ssss
    search_expanded = False
    es_query = es_and(and_terms, filters)
    hits = self._search(es_query, sort, query.page_num)

    result = Result(query, hits)
    os.environ.get('DEBUG','') and (print(result)) # ssss
    return result

  def _search(self, es_query, sort, page_num):
    body = {
      "query": es_query,
      "sort": sort,
      "from": page_num * self.page_size,
      "size": self.page_size + 1
    }
    os.environ.get('DEBUG','') and (print(self.index), print(json.dumps(body,indent=2))) # ssss
    search_response = self.es.search(index=self.index, body=body)
    # Just return the list of results.
    return search_response['hits']['hits']

  def tokenize(self, s):
    if not s:
      return []
    # Split `s` using the search_analyser.
    body = {'analyzer': 'search_analyser', 'text': s}
    response = self.es.indices.analyze(index=self.index, body=body)
    return [token['token'] for token in response['tokens']]

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

# Document contains all the terms in any order, with fuzziness.

# {
#   "match": {
#     "full_title": {
#       "query": query.search,
#       "operator": "and",
#       "fuzziness": "AUTO",
#       "boost": 10
#     }
#   }
# },
