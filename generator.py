#!/usr/bin/env python3

import unicodedata
import re
import os
import datetime
from jinja2 import Environment, FileSystemLoader
from typing import List, Any, Dict, Optional
from mbutils import *
from model import *
from db import *

OUTPUT_DIR = 'site'
DOMAIN='https://nytspellingbeesolver.com'
HOST=os.environ.get('HOST', DOMAIN)
PER_PAGE=50


def url(path: str) -> str:
  host = HOST
  if host[-1] != '/' and path[0] != '/':
    host += '/'
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

class Generator:
  def __init__(self):
    self.db = DB()
    self.env = Environment(loader=FileSystemLoader('templates'))
    self.env.globals.update(
      domain=DOMAIN,
      format_date=format_date,
      sort_by_clue=sort_by_clue,
      format_letters=format_letters)
    mkdir(OUTPUT_DIR)

  def generate_all(self) -> None:
    self.generate_puzzles()
    self.generate_clue_pages()
    self.generate_main()
    self.generate_sitemap()
    self.generate_archives()
    self.generate_static()

  def generate_puzzles(self) -> None:
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


  skip = ['static/input.css']
  special = {'static/robots.txt': f'{OUTPUT_DIR}/robots.txt'}
  duplicate = {
    'static/favicon/favicon.ico': f'{OUTPUT_DIR}/favicon.ico',
  }
  def generate_static(self) -> None:
    shell(f'npx tailwindcss -i ./static/input.css -o {OUTPUT_DIR}/static/style.css')

    for file in ls('static/*'):
      filename = file.replace('static/', '', 1)

      dest = OUTPUT_DIR + '/static/' + filename
      if file in self.special:
        dest = self.special[file]
      if file not in self.skip:
        cp_file(file, dest)

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
