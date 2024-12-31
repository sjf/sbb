#!/usr/bin/env python3

import unicodedata
import re
import os
from jinja2 import Environment, FileSystemLoader
from typing import List, Any, Dict, Optional
from mbutils import *
from model import *
from db import *

OUTPUT_DIR = 'site'
HOST='http://box:8081/'
DEV=os.environ.get('DEV',None)

def output(location: str, contents: str) -> None:
  path = OUTPUT_DIR + '/' + location
  write(path, contents, create_dirs = True)
  log(f"Generated {HOST}{location}")

def puzzle_url(puzzle: GPuzzle) -> str:
  return f"puzzle/{puzzle.date}"

class Generator:
  def __init__(self):
    self.db = DB()
    self.env = Environment(loader=FileSystemLoader('templates'))
    self.env.globals.update(date_format=date_format, DEV=DEV)
    mkdir(OUTPUT_DIR)

  def generate_all(self) -> None:
    #self.generate_puzzles()
    #self.generate_clue_pages()
    self.generate_main()
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
    latest_dates = self.db.fetch_latest_puzzle_dates(8)
    latest_dates = latest_dates.remove(latest.date)
    # latest_dates = sorted(set(latest_dates) - set(),reverse=True)
    rendered = template.render(puzzle=latest, past_dates=latest_dates)
    output('index.html', rendered)

  skip = ['static/input.css', 'static/custom.css']
  duplicate = {
    'static/favicon/favicon.ico': f'{OUTPUT_DIR}/favicon.ico',
  }
  def generate_static(self) -> None:
    # if not DEV:
    shell(f'npx tailwindcss -i ./static/input.css -o {OUTPUT_DIR}/static/style.css')

    for file in ls('static/*'):
      filename = file.replace('static/', '', 1)

      if file not in self.skip:
        dest = OUTPUT_DIR + '/static/' + filename
        cp_file(file, dest)

    for file, dest in self.duplicate.items():
      cp_file(file, dest)

def cp_file(file: str, dest: str) -> None:
  shell(f'cp -a {file} {dest}', verbose=False)
  path = dest.replace(OUTPUT_DIR + '/', '', 1)
  log(f"Copied {file} to {HOST}{path}")

if __name__ == '__main__':
  generator = Generator()
  generator.generate_all()
