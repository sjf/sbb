#!/usr/bin/env python3

import unicodedata
import re
import os
import datetime
from collections import defaultdict
from http import HTTPStatus
from jinja2 import Environment, FileSystemLoader
from typing import List, Any, Dict, Optional
from mbutils import *
from model import *
from db import *

OUTPUT_DIR = 'site'
DOMAIN=os.environ.get('DOMAIN', 'https://beekey.buzz')
DEV=os.environ.get('DEV', False)
VERSION=2
PER_PAGE=50
TODAY = datetime.datetime.now().strftime('%Y-%m-%d')

def joinp(a: str, b: str) -> str:
  if a[-1] != '/' and b[0] != '/':
    a += '/'
  if a[-1] == '/' and b[0] == '/':
    a = a[:-1]
  return a + b

def url(path: str) -> str:
  return joinp(DOMAIN, path)

def cp_file(file: str, dest: str) -> None:
  dirs = dirname(dest)
  mkdir(dirs)
  shell(f'cp -a {file} {dest}', verbose=False)
  path = dest.replace(OUTPUT_DIR + '/', '', 1)
  log(f"Copied {file} to {url(path)}")


def url_for(o: Any) -> str:
  if type(o) == GPuzzle:
    return f"/puzzle/{o.date}"
  if type(o) == str and re.match(r'^\d\d\d\d-\d\d-\d\d$', o):
    # link to puzzle by date
    return f"/puzzle/{o}"
  if type(o) == str and re.match(r'^\d\d\d\d-\d\d$', o):
    # link to puzzle archive by month and year
    return '/puzzles/' + o.replace('-', '/')
  raise Exception(f"Unhandled url_for {o}")

def json_esc(s: str) -> str:
  return json.dumps(s)[1:-1]

class Generator:
  def __init__(self):
    self.db = DB()
    self.env = Environment(loader=FileSystemLoader('templates'))
    self.env.globals.update(
      domain=DOMAIN,
      DEV=DEV,
      VERSION=VERSION,
      current_year=datetime.datetime.now().year,
      url_for=url_for,
      format_date=format_date,
      sort_by_clue=sort_by_clue,
      joinl=joinl)
    self.env.filters['json_esc'] = json_esc
    self.pages = []

  def generate_all(self) -> None:
    self.generate_main()
    self.generate_clue_pages()
    self.generate_archives()
    self.generate_puzzle_archives()
    self.generate_puzzle_pages()
    # These have to be last.
    self.generate_sitemap()
    self.generate_static()

  def output(self, location: str, contents: str, lastmod: Optional[str], is_internal: bool=False) -> None:
    path = joinp(OUTPUT_DIR, location)
    write(path, contents, create_dirs = True)
    if not is_internal:
      self.pages.append(Page(path=location, lastmod=lastmod))
    log(f"Generated {url(location)}")

  def ln(self, src: str, dest: str, lastmod: str) -> None:
    log(f"Linking {src} -> {dest} lastmod:{lastmod}")
    src_file = realpath(joinp(OUTPUT_DIR, src))
    dest_file = realpath(joinp(OUTPUT_DIR, dest))
    log(f"Linking {src_file} -> {dest_file}")
    ln(src_file, dest_file)
    self.pages.append(Page(path=dest, lastmod=lastmod))
    log(f"Generated {url(dest)}")

  def generate_puzzle_pages(self) -> None:
    template = self.env.get_template('puzzle.html')
    puzzles = self.db.fetch_gpuzzles()
    for puzzle in puzzles:
      rendered = template.render(puzzle=puzzle)
      self.output(url_for(puzzle), rendered, puzzle.date)
    latest = puzzles[0]
    self.ln(url_for(latest), '/puzzle/latest', latest.date)

  def generate_clue_pages(self) -> None:
    template = self.env.get_template('clue_page.html')
    clue_pages = self.db.fetch_gclue_pages()
    for page in clue_pages:
      rendered = template.render(page=page)
      self.output(page.url, rendered, page.answers[0].puzzle_date)

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
    latest_dates = self.db.fetch_latest_puzzle_dates(14)
    latest_dates.remove(latest.date)
    # latest_dates = sorted(set(latest_dates) - set(),reverse=True)
    rendered = template.render(puzzle=latest, past_dates=latest_dates)
    self.output('index.html', rendered, TODAY)

    template = self.env.get_template('about.html')
    rendered = template.render()
    self.output('about', rendered, '2025-01-01')

    template = self.env.get_template('error.html')
    for code,message in self.error_messages.items():
      status = HTTPStatus(code).phrase
      rendered = template.render(code=code, status=status, message=message)
      self.output(f'error/{code}.html', rendered, None, is_internal=True)

  def generate_archives(self) -> None:
    template = self.env.get_template('clue_archive.html')
    answers = self.db.fetch_ganswers()
    answers = filter(lambda x:x.text, answers) # remove answers without clues.
    answers = sorted(answers, key=lambda x:x.text)

    for page in range(1, total_pages(answers) + 1):
      rendered = template.render(pagination=Pagination(items=answers, page=page, per_page=PER_PAGE), n=3)
      self.output(f'clue-archive/{page}', rendered, TODAY)

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
      path = '/puzzles/' + yearmonth.replace('-', '/')
      lastmod = max(map(lambda x:x.date, puzzles))

      rendered = template.render(puzzles=puzzles, period=period, pagination=PaginationBar(pages=pages, current=path))
      self.output(path, rendered, lastmod)

    lastmod = sorted(by_yearmonth[latest])[0].date
    self.ln(latest_page, '/puzzles/latest', lastmod)

  def generate_sitemap(self) -> None:
    if len(self.pages) > 50_000 - 300:
      log_error(f"Site map is close maximum size of 50k: {len(self.pages)}")
    template = self.env.get_template('sitemap.xml')
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
      filename = file.replace('static/', '', 1)

      dest = OUTPUT_DIR + '/static/' + filename
      if file in self.special:
        dest = self.special[file]
      if file not in self.skip:
        cp_file(file, dest)

    for file in ls("secrets/*.txt"):
      # Copy indexnow api key
      cp_file(file, f'{OUTPUT_DIR}/{basename(file)}')
    # Copy more files that need to be copied to multiple places
    for file, dest in self.duplicate.items():
      cp_file(file, dest)

def total_pages(items):
  return ceil(len(items) / PER_PAGE)

@dataclass
class Page:
  path: str
  lastmod: Optional[str]

if __name__ == '__main__':
  generator = Generator()
  generator.generate_all()
