import json
from typing import List, Any, Dict, Optional
from jinja2 import Environment
from pyutils.settings import config
from pyutils import *
from model import *

def set_env_globals(env: Environment) -> None:
  env.globals.update(
    DEV=config['DEV'],
    domain=config['DOMAIN'],
    VERSION=config['VERSION'],
    config=config,
    current_year=datetime.datetime.now().year,
    url_for=url_for,
    format_date=format_date,
    sort_by_clue=sort_by_clue,
    joinl=joinl,
    split_by_start=split_by_start,
    get_content_group=get_content_group)
  env.filters['json_esc'] = lambda s:json.dumps(s)[1:-1]

def url_for(o: Any, arg=None) -> str:
  if type(o) == GPuzzle:
    return f"/puzzle/{o.date}"

  if type(o) == str and re.match(r'^\d\d\d\d-\d\d-\d\d$', o):
    # link to puzzle by date
    return f"/puzzle/{o}"

  if type(o) == str and re.match(r'^\d\d\d\d-\d\d$', o):
    # link to puzzle archive by month and year
    return '/puzzles/' + o.replace('-', '/')

  if type(o) == GAnswer:
    if not o.url:
      raise Exception(f"Cannot create url for answer with no clue url: {o}")
    return o.url

  if o == 'clues':
    if not arg:
      raise Exception("Unhandled url, clues archive needs arg")
    return '/clues/' + arg

  if type(o) == GWordDefinition:
    return f"/definition/{o.word}"

  raise Exception(f"Unhandled url_for '{o}' arg={arg}")

def get_content_group(url: str) -> str:
  prefixes = {
    '/index.html':     'Home Page',

    '/puzzle/latest':  'Latest Puzzle',
    '/puzzle/':        'Puzzle Page',
    '/puzzles/latest': 'Latest Puzzle',
    '/puzzles/':       'Puzzle Archive',

    '/clue/':          'Clue Page',
    '/clues/':         'Clue Archive',

    '/definition/':    'Definition',

    '/search':         'Search Results',

    '/about':          'About',
    '/error/':         'Error Page',
  }
  path = url_path(url)
  for prefix,content_group in prefixes.items():
    if path.startswith(prefix):
      return content_group
  if path == '/':
    return 'Home Page'
  raise Exception(f'No content group for {url}')

def format_date(value: str) -> str:
  date = datetime.datetime.strptime(value, "%Y-%m-%d")
  return date.strftime("%B %-d, %Y")

def split_by_start(l: List[GAnswer]) -> List[List[GAnswer]]:
  # Split up the words by their first letter.
  l = sorted(l)
  d = defaultdict(list)
  for a in l:
    d[a.word[0]].append(a)
  return sorted(d.values())

def sort_by_clue(answers: List[GAnswer]) -> List[GAnswer]:
  return sorted(answers, key=lambda x: (x.word[0], len(x.word)))


