#!/usr/bin/env python3

import unicodedata
import re
import os
import datetime
import htmlmin
from collections import defaultdict
from http import HTTPStatus
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from typing import List, Any, Dict, Optional
from pyutils import settings
from pyutils import *
from jinja_util import *
from model import *
from db import *

SITE_DIR = settings.config['OUTPUT_DIR']
OUTPUT_DIR = joinp(SITE_DIR, f"sbb-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}")
DOMAIN = settings.config['DOMAIN']
VERSION = settings.config['VERSION']
DEV = settings.config['DEV']
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
    log(f"Generating: {OUTPUT_DIR}")
    log(f"Config:\n{dictl(config)}")
    self.generate_main()
    self.generate_clue_pages()
    self.generate_clue_archives()
    self.generate_puzzle_archives()
    self.generate_puzzle_pages()
    self.generate_definitions()

    # These have to be last.
    self.generate_sitemap()
    self.generate_static()
    self.switch_to_serving()

  def switch_to_serving(self) -> None:
    log(f"*** Switching serving '{config['SERVING_DEST']}' to '{OUTPUT_DIR}' ***")
    self.rel_ln(OUTPUT_DIR, config['SERVING_DEST'])

    dirs = ls(f'{SITE_DIR}/sbb-*')
    dirs = sorted(dirs, reverse=True)
    for d in dirs[6:]: # keep last six generations
      log(f"Removing old generated site {d}")
      rm_rf(d)

  def output(self, location: str, contents: str, lastmod: Optional[str], is_internal: bool=False) -> None:
    if not DEV and config['HTML_MIN']: # Only in prod and when enable because this is slow.
      if contents.startswith('<!DOCTYPE html>') or contents.startswith('<html>'):
        contents = htmlmin.minify(contents,
          remove_comments=True,        # Remove all HTML comments
          remove_empty_space=True,     # Collapse unnecessary whitespace
          remove_all_empty_space=False,  # Preserve essential spaces in inline elements
          reduce_boolean_attributes=False,  # Keep `checked="checked"` for compatibility
          remove_optional_attribute_quotes=False)  # Keep quotes around attributes for safety

    path = joinp(OUTPUT_DIR, location)
    write(path, contents, create_dirs = True)
    if not is_internal:
      # Add to site map
      self.pages.append(Page(path=location, lastmod=lastmod))
    log_debug(f"Generated {url(location)}")

  def ln(self, src: str, dst: str, lastmod: str, is_internal: bool=False) -> None:
    log(f"Linking {src} -> {dst} lastmod:{lastmod}")
    src_path = joinp(OUTPUT_DIR, src)
    dst_path = joinp(OUTPUT_DIR, dst)

    self.rel_ln(src_path, dst_path)

    if not is_internal:
      self.pages.append(Page(path=dst, lastmod=lastmod))
    log(f"Generated {url(dst)}")

  def rel_ln(self, src_path: str, dst_path: str) -> None:
    # For serving to work properly they both need to be under the base OUTPUT_DIR.
    base_output = realpath(SITE_DIR)
    src_path = realpath(src_path)
    dst_path = realpath(dst_path)
    # print(src_path, dst_path, base_output)
    assert src_path.startswith(base_output)
    assert dst_path.startswith(base_output)

    common_dir = os.path.commonpath([src_path, dst_path])
    rel_src_path = src_path[len(common_dir)+1:]
    rel_dst_path = dst_path[len(common_dir)+1:]

    saved_dir = os.getcwd()
    os.chdir(common_dir)
    log(f"Linking relative {rel_src_path} -> {rel_dst_path} in {common_dir}.")
    ln(rel_src_path, rel_dst_path)
    os.chdir(saved_dir)

  def generate_puzzle_pages(self) -> None:
    template = self.env.get_template('puzzle.html')
    puzzles = self.db.fetch_gpuzzles()
    max_date = puzzles[0].date
    min_date = puzzles[-1].date
    for i, puzzle in enumerate(puzzles):
      url = url_for(puzzle)
      next_ = None
      if i > 0:
        next_ = puzzles[i-1]
      prev = None
      if i < len(puzzles) - 1:
        prev = puzzles[i+1]
      rendered = template.render(url=url,
        canon_url=url_for(puzzle),
        puzzle=puzzle,
        next_=next_,
        prev=prev,
        min_date=min_date,
        max_date=max_date)
      self.output(url, rendered, puzzle.date)
    latest = puzzles[0]
    self.ln(url_for(latest), '/puzzle/latest', latest.date)

  def generate_clue_pages(self) -> None:
    template = self.env.get_template('clue_page.html')
    clue_pages = self.db.fetch_gclue_pages()
    for page in clue_pages:
      url = page.url
      rendered = template.render(url=url, canon_url=url, page=page)
      self.output(url, rendered, page.clue_answers[0].puzzle_dates[0])

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
    puzzles = self.db.fetch_gpuzzles()
    latest = puzzles[0]
    prev = puzzles[1]
    max_date = puzzles[0].date
    min_date = puzzles[-1].date
    rendered = template.render(url='/index.html',
      canon_url=url_for(latest),
      puzzle=latest,
      prev=prev,
      next_=None,
      max_date=max_date,
      min_date=min_date)
    self.output('/index.html', rendered, TODAY)

    template = self.env.get_template('about.html')
    rendered = template.render(url='/about', canon_url='/about')
    self.output('/about', rendered, '2025-01-01')

    template = self.env.get_template('internal/error.html')
    for code,message in self.error_messages.items():
      status = HTTPStatus(code).phrase
      url = f'/error/{code}.html'
      rendered = template.render(url=url, code=code, status=status, message=message)
      self.output(url, rendered, None, is_internal=True)

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
      answers = sorted(answers, key=lambda x:x.text)
      lastmod = max(map(lambda x:x.puzzle_date, answers))
      url = url_for('clues', prefix)
      rendered = template.render(
        url=url,
        answers=answers,
        prefix=prefix,
        alphabet=prefixes,
        pagination=PaginateList(pages=pages, current=url),
        canon_url=url)
      self.output(url, rendered, lastmod)

  def generate_puzzle_archives(self) -> None:
    # Group puzzles by year and month
    by_yearmonth = defaultdict(list)
    for puzzle in self.db.fetch_gpuzzles():
      yearmonth = puzzle.date.rsplit('-', 1)[0]
      by_yearmonth[yearmonth].append(puzzle)

    # All the archive pages for each mont.
    pages = mapl(url_for, by_yearmonth.keys())
    pages = sorted(pages, reverse=True)

    template = self.env.get_template('puzzle_archive.html')
    for yearmonth, puzzles in by_yearmonth.items():
      puzzles = sorted(puzzles, reverse=True)
      period = format_yearmonth(yearmonth)
      url = url_for(yearmonth)
      lastmod = max(map(lambda x:x.date, puzzles))
      rendered = template.render(
        url=url,
        canon_url=url,
        puzzles=puzzles,
        period=period,
        pagination=PaginateList(pages=pages, current=url))
      self.output(url, rendered, lastmod)

    latest = sorted(by_yearmonth.keys())[-1]
    latest_path = url_for(latest)
    lastmod = by_yearmonth[latest][0].date
    log(f'Latest archive page: {latest_path} last mod: {lastmod}')
    self.ln(latest_path, '/puzzles/latest', lastmod)

  def generate_definitions(self) -> None:
    words = self.db.fetch_gwords()
    template = self.env.get_template('word_definition.html')
    lastmod = "2025-01-01" # Just used a fixed date.
    for word in words:
      url = url_for(word)
      rendered = template.render(
        url=url,
        canon_url=url_for(word),
        word=word.word,
        definition=word.definition,
        lastmod=lastmod)
      self.output(url, rendered, lastmod)

  def generate_sitemap(self) -> None:
    if len(self.pages) > 50_000 - 300:
      log_error(f"Site map is close maximum size of 50k links: {len(self.pages)}")
    template = self.env.get_template('internal/sitemap.xml')
    rendered = template.render(pages=self.pages)
    self.output('sitemap.xml', rendered, None, is_internal=True)

  def generate_static(self) -> None:
    if not DEV:
      shell(f'npx tailwindcss -i input.css -o {OUTPUT_DIR}/static/style.{VERSION}.css --minify')
      shell(f'terser static_files/static/script.js --mangle -o {OUTPUT_DIR}/static/script.{VERSION}.min.js')
    else:
      mkdir(f'{OUTPUT_DIR}/static/')
      cp('static_files/static/script.js',  f'{OUTPUT_DIR}/static/script.{VERSION}.js')
      cp('static_files/static/custom.css', f'{OUTPUT_DIR}/static/custom.{VERSION}.css')

    for file in ls('static_files/*'):
      cp_file(file, OUTPUT_DIR)

@dataclass
class Page:
  path: str
  lastmod: Optional[str]

if __name__ == '__main__':
  generator = Generator()
  generator.generate_all()
