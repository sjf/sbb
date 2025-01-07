#!/usr/bin/env python3

import unicodedata
import re
import os
import datetime
from http import HTTPStatus
from jinja2 import Environment, FileSystemLoader
from typing import List, Any, Dict, Optional
from mbutils import *
from model import *
from db import *

OUTPUT_DIR = 'site'
DOMAIN=os.environ.get('DOMAIN', 'https://beekey.buzz')
DEV=os.environ.get('DEV', False)
VERSION=1
PER_PAGE=50

def url(path: str) -> str:
  host = DOMAIN
  if host[-1] != '/' and path[0] != '/':
    host += '/'
  if host[-1] == '/' and path[0] == '/':
    host = host[:-1]
  return f"{host}{path}"

def output(location: str, contents: str) -> None:
  path = OUTPUT_DIR + '/' + location
  write(path, contents, create_dirs = True)
  log(f"Generated {url(location)}")

def cp_file(file: str, dest: str) -> None:
  shell(f'cp -a {file} {dest}', verbose=False)
  path = dest.replace(OUTPUT_DIR + '/', '', 1)
  log(f"Copied {file} to {url(path)}")


def puzzle_url(puzzle: GPuzzle) -> str:
  return f"puzzle/{puzzle.date}"

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
      format_date=format_date,
      sort_by_clue=sort_by_clue,
      joinl=joinl)
    self.env.filters['json_esc'] = json_esc
    mkdir(OUTPUT_DIR)

  def generate_all(self) -> None:
    self.generate_sitemap()
    self.generate_archives()
    self.generate_puzzle_pages()
    self.generate_clue_pages()
    self.generate_main()
    # This has to be last.
    self.generate_static()

  def generate_puzzle_pages(self) -> None:
    template = self.env.get_template('puzzle.html')
    puzzles = self.db.fetch_gpuzzles()
    for puzzle in puzzles:
      rendered = template.render(puzzle=puzzle)
      output(puzzle_url(puzzle), rendered)

  def generate_clue_pages(self) -> None:
    template = self.env.get_template('clue_page.html')
    clue_pages = self.db.fetch_gclue_pages()
    for page in clue_pages:
      rendered = template.render(page=page)
      output(page.url, rendered)

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
    output('index.html', rendered)

    template = self.env.get_template('about.html')
    rendered = template.render()
    output('about', rendered)

    template = self.env.get_template('error.html')
    for code,message in self.error_messages.items():
      status = HTTPStatus(code).phrase
      rendered = template.render(code=code, status=status, message=message)
      output(f'error/{code}.html', rendered)

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
      shell(f'npx tailwindcss -i ./static/input.css -o {OUTPUT_DIR}/static/style.{VERSION}.css')

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

  def generate_sitemap(self) -> None:
    template = self.env.get_template('sitemap.xml')
    clue_pages = self.db.fetch_gclue_pages()
    puzzles = self.db.fetch_gpuzzles()
    current_date = datetime.datetime.today().strftime('%Y-%m-%d')
    answers = self.db.fetch_ganswers()
    num_clue_archive_pages = total_pages(answers)
    rendered = template.render(
      puzzles=puzzles,
      clue_pages=clue_pages,
      num_clue_archive_pages=num_clue_archive_pages,
      current_date=current_date)
    output('sitemap.xml', rendered)

  def generate_archives(self) -> None:
    template = self.env.get_template('clue_archive.html')
    answers = self.db.fetch_ganswers()
    answers = filter(lambda x:x.text, answers) # remove answers without clues.
    answers = sorted(answers, key=lambda x:x.text)

    for page in range(1, total_pages(answers) + 1):
      rendered = template.render(pagination=Pagination(items=answers, page=page, per_page=PER_PAGE), n=3)
      output(f'clue-archive/{page}', rendered)

    template = self.env.get_template('puzzle_archive.html')
    puzzles = self.db.fetch_gpuzzles()
    rendered = template.render(puzzles=puzzles)
    output('puzzle-archive', rendered)

def total_pages(items):
  return ceil(len(items) / PER_PAGE)

if __name__ == '__main__':
  generator = Generator()
  generator.generate_all()
