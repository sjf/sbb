#!/usr/bin/env python3

import unicodedata
import re
import os
import datetime
from collections import defaultdict
from http import HTTPStatus
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from typing import List, Any, Dict, Optional
from pyutils import settings
from pyutils import *
from model import *
from db import *

OUTPUT_DIR = settings.config['OUTPUT_DIR']
DOMAIN = settings.config['DOMAIN']
VERSION = settings.config['VERSION']
DEV = bool(os.environ.get('DEV', False))
TODAY = datetime.datetime.now().strftime('%Y-%m-%d')

def url(path: str) -> str:
  return joinp(DOMAIN, path)

def cp_file(file: str, dest: str) -> None:
  dirs = dirname(dest)
  if dirs:
    mkdir(dirs)
  shell(f'cp -a {file} {dest}', verbose=False)

  url_path = dest.replace(OUTPUT_DIR + '/', '', 1)
  if is_dir(dest):
    url_path = joinp(url_path,basename(file))
  log(f"Copied {file} to {url(url_path)}")

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

def split_by_start(l: List[GAnswer]) -> List[List[GAnswer]]:
  l = sorted(l)
  d = defaultdict(list)
  for a in l:
    d[a.word[0]].append(a)
  return sorted(d.values())

def set_env_globals(env: Environment) -> None:
  env.globals.update(
    domain=DOMAIN,
    DEV=DEV,
    VERSION=VERSION,
    current_year=datetime.datetime.now().year,
    url_for=url_for,
    format_date=format_date,
    sort_by_clue=sort_by_clue,
    joinl=joinl,
    split_by_start=split_by_start)
  env.filters['json_esc'] = lambda s:json.dumps(s)[1:-1]

class Generator:
  def __init__(self):
    self.db = DB()
    self.env = Environment(
      loader=FileSystemLoader('templates'),
      undefined=StrictUndefined,
      trim_blocks=(not DEV),
      lstrip_blocks=(not DEV))
    set_env_globals(self.env)
    self.pages = []

  def generate_all(self) -> None:
    self.generate_main()
    self.generate_clue_pages()
    self.generate_clue_archives()
    self.generate_puzzle_archives()
    self.generate_puzzle_pages()
    self.generate_definitions()
    # These have to be last.
    self.generate_sitemap()
    self.generate_static()

  def output(self, location: str, contents: str, lastmod: Optional[str], is_internal: bool=False) -> None:
    path = joinp(OUTPUT_DIR, location)
    write(path, contents, create_dirs = True)
    if not is_internal:
      self.pages.append(Page(path=location, lastmod=lastmod))
    log(f"Generated {url(location)}")

  def ln(self, src: str, dst: str, lastmod: str) -> None:
    log(f"Linking {src} -> {dst} lastmod:{lastmod}")
    src_path = realpath(joinp(OUTPUT_DIR, src))
    dst_path = realpath(joinp(OUTPUT_DIR, dst))

    common_dir = os.path.commonpath([src_path, dst_path]) # This is guaranteed to be in the OUTPUT_DIR
    saved_dir = os.getcwd()
    os.chdir(common_dir)

    rel_src_path = src_path[len(common_dir)+1:]
    rel_dst_path = dst_path[len(common_dir)+1:]

    log(f"Linking relative {rel_src_path} -> {rel_dst_path} in {common_dir}.")
    ln(rel_src_path, rel_dst_path)
    os.chdir(saved_dir)

    self.pages.append(Page(path=dst, lastmod=lastmod))
    log(f"Generated {url(dst)}")

  def generate_puzzle_pages(self) -> None:
    template = self.env.get_template('puzzle.html')
    puzzles = self.db.fetch_gpuzzles()
    for puzzle in puzzles:
      rendered = template.render(puzzle=puzzle, canon_url=url_for(puzzle))
      self.output(url_for(puzzle), rendered, puzzle.date)
    latest = puzzles[0]
    self.ln(url_for(latest), '/puzzle/latest', latest.date)

  def generate_clue_pages(self) -> None:
    template = self.env.get_template('clue_page.html')
    clue_pages = self.db.fetch_gclue_pages()
    for page in clue_pages:
      rendered = template.render(page=page, canon_url=page.url)
      self.output(page.url, rendered, page.clue_answers[0].puzzle_dates[0])

  error_messages = {
      400: "Your request could not be processed. Please check the URL or try again later.",
      403: "Access denied. You don't have permission to view this page.",
      404: "We couldn't find the page you were looking for.",
      500: "Something went wrong on our end. Please try again later.",
      502: "The server received an invalid response from the upstream server.",
      503: "The server is temporarily unable to handle the request. Please try again later."
  }
  def generate_main(self) -> None:
    template = self.env.get_template('index.html')
    latest = self.db.fetch_latest_gpuzzle()
    latest_dates = self.db.fetch_latest_puzzle_dates(4)
    latest_dates.remove(latest.date)
    # latest_dates = sorted(set(latest_dates) - set(),reverse=True)
    rendered = template.render(puzzle=latest, past_dates=latest_dates, canon_url=url_for(latest))
    self.output('/index.html', rendered, TODAY)

    template = self.env.get_template('about.html')
    rendered = template.render(canon_url='/about')
    self.output('/about', rendered, '2025-01-01')

    template = self.env.get_template('internal/error.html')
    for code,message in self.error_messages.items():
      status = HTTPStatus(code).phrase
      rendered = template.render(code=code, status=status, message=message)
      self.output(f'/error/{code}.html', rendered, None, is_internal=True)

  @staticmethod
  def get_clue_archive_prefix(text: str) -> str:
    text = re.sub('^[\'"“”‘ ]+', '', text) # Remove quotes and whitespace.
    # Try to normalize unicode to ascii, fall back to original character.
    cs = []
    for c in text:
      c2 = unicodedata.normalize('NFKD', c).encode('ascii', 'ignore').decode('ascii') or c
      cs.append(c2)
    text = ''.join(cs)
    text = text.lower() # URLs use lowercase, uppercase is only used for display.

    prefix = text[0:1]
    if prefix.isalpha() and prefix.isascii():
      return prefix
    if prefix.isdigit():
      return '0-9'
    else:
      return 'symbols'

  def generate_clue_archives(self) -> None:
    answers = self.db.fetch_ganswers()
    answers = filter(lambda x:x.text and x.url, answers) # remove answers without clues.
    by_prefix = defaultdict(list)
    for answer in answers:
      prefix = Generator.get_clue_archive_prefix(answer.text)
      by_prefix[prefix].append(answer)

    # How the prefixes are sorted, letters, then numbers, then rest.
    def prefix_key(prefix):
      if len(prefix) == 1 and prefix.isalpha() and prefix.isascii():
        return (0, prefix)
      elif prefix.isdigit():
        return (1, prefix)
      else:
        return (2, prefix)

    prefixes = sorted(by_prefix.keys(), key=prefix_key)
    pages = mapl(lambda p:url_for('clues', p), prefixes)

    template = self.env.get_template('clue_archive.html')
    for prefix, answers in sorted(by_prefix.items(), key=lambda x:prefix_key(x[0])):
      path = url_for('clues', prefix)
      answers = sorted(answers, key=lambda x:x.text)
      lastmod = max(map(lambda x:x.puzzle_date, answers))
      rendered = template.render(
        answers=answers,
        prefix=prefix,
        alphabet=prefixes,
        pagination=PaginateList(pages=pages, current=path),
        canon_url=path)
      self.output(path, rendered, lastmod)

  def generate_puzzle_archives(self) -> None:
    by_yearmonth = defaultdict(list)
    for puzzle in self.db.fetch_gpuzzles():
      yearmonth = puzzle.date.rsplit('-', 1)[0]
      by_yearmonth[yearmonth].append(puzzle)

    latest = sorted(by_yearmonth.keys())[-1]
    latest_page = url_for(latest)
    pages = mapl(url_for, by_yearmonth.keys())
    pages = sorted(pages, reverse=True)

    template = self.env.get_template('puzzle_archive.html')
    for yearmonth, puzzles in by_yearmonth.items():
      period = format_yearmonth(yearmonth)
      path = url_for(yearmonth)
      lastmod = max(map(lambda x:x.date, puzzles))

      rendered = template.render(
        puzzles=puzzles,
        period=period,
        pagination=PaginateList(pages=pages, current=path),
        canon_url=path)
      self.output(path, rendered, lastmod)

    lastmod = sorted(by_yearmonth[latest])[0].date
    self.ln(latest_page, '/puzzles/latest', lastmod)

  def generate_definitions(self) -> None:
    words = self.db.fetch_gwords()
    template = self.env.get_template('word_definition.html')
    lastmod = "2025-01-01" # Just used a fixed date.
    for word in words:
      rendered = template.render(
        word=word.word,
        definition=word.definition,
        canon_url=url_for(word),
        lastmod=lastmod)
      self.output(url_for(word), rendered, lastmod)

  def generate_sitemap(self) -> None:
    if len(self.pages) > 50_000 - 300:
      log_error(f"Site map is close maximum size of 50k links: {len(self.pages)}")
    template = self.env.get_template('internal/sitemap.xml')
    rendered = template.render(pages=self.pages)
    self.output('sitemap.xml', rendered, None, is_internal=True)

  skip = ['static/input.css']
  special = {
    'static/robots.txt': f'{OUTPUT_DIR}/robots.txt',
    'static/script.js': f'{OUTPUT_DIR}/static/script.{VERSION}.js',
    'static/custom.css': f'{OUTPUT_DIR}/static/custom.{VERSION}.css',
  }
  duplicate = {
    'static/favicon/favicon.ico': f'{OUTPUT_DIR}/favicon.ico',
  }
  def generate_static(self) -> None:
    if not DEV:
      shell(f'npx tailwindcss -i ./static/input.css -o {OUTPUT_DIR}/static/style.{VERSION}.css --minify')
      shell(f'terser static/script.js --mangle -o {OUTPUT_DIR}/static/script.{VERSION}.min.js')

    for file in ls('static/*'):
      dest = joinp(OUTPUT_DIR, 'static/')
      if file in self.special:
        dest = self.special[file]
      if file not in self.skip:
        cp_file(file, dest)

    # Copy more files that need to be copied to multiple places
    for file, dest in self.duplicate.items():
      cp_file(file, dest)

@dataclass
class Page:
  path: str
  lastmod: Optional[str]

if __name__ == '__main__':
  generator = Generator()
  generator.generate_all()
