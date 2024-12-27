#!/usr/bin/env python3

import unicodedata
import re
from jinja2 import Environment, FileSystemLoader
from typing import List, Any, Dict, Optional
from mbutils import *
from model import *
from db import *

OUTPUT_DIR = 'site'
HOST='http://box:8081/'

def clue_url(clue: GClue) -> str:
  # return f"clue/{clue.id}"
  safe_text = to_path_safe_name(clue.text)
  url = f"clue/{safe_text}"
  dest = OUTPUT_DIR + "/" + url
  if exists(dest):
    log_fatal(f"Cannot create page for {clue}, already exists: {dest}")
  return url

def to_path_safe_name(text: str, max_length: int = 100) -> str:
  # Normalize to ASCII (remove accents)
  text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
  # Replace non-alphanumeric characters with hyphens
  text = re.sub(r'[^a-zA-Z0-9\s-]', '-', text)
  # Replace spaces and multiple hyphens with a single hyphen
  text = re.sub(r'[\s-]+', '-', text).strip('-')
  # Lowercase the final string
  text = text.lower()
  if len(text) > max_length:
    text = text[:max_length].rsplit('-', 1)[0] # Split at hyphen.
  return text

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
    mkdir(OUTPUT_DIR)

  def generate_all(self) -> None:
    self.generate_puzzles()
    self.generate_clue_pages()
    self.generate_main()

  def generate_puzzles(self) -> None:
    template = self.env.get_template('puzzle.html')
    puzzles = self.db.fetch_gpuzzles()
    for puzzle in puzzles:
      rendered = template.render(puzzle=puzzle)
      output(puzzle_url(puzzle), rendered)

  def generate_clue_pages(self) -> None:
    template = self.env.get_template('clue.html')
    clue_pages = self.db.fetch_gclue_pages()
    for page in clue_pages:
      rendered = template.render(page=page)
      output(page.url, rendered)

  def generate_main(self) -> None:
    template = self.env.get_template('index.html')
    latest = self.db.fetch_latest_gpuzzle()
    rendered = template.render(puzzle=latest)
    output('index.html', rendered)

if __name__ == '__main__':
  generator = Generator()
  generator.generate_all()
