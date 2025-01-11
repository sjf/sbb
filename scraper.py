#!/usr/bin/env python
from mbutils import *
from requester import *

ACTIVE_URL = "https://www.nytimes.com/svc/spelling-bee/v1/active.json"
CLUES_URL = "https://static01.nyt.com/newsgraphics/2023-01-18-spelling-bee-buddy/clues/{id_}.json"
STATS_URL = "https://static01.nyt.com/newsgraphics/2023-01-18-spelling-bee-buddy/stats/{id_}.json"

DIR = "scraped"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
SLEEP = 0.1

class Scraper:
  def __init__(self):
    self.requester = Requester(user_agent=USER_AGENT, sleep=SLEEP)

  def setup(self):
    if not exists_dir(DIR):
      return mkdir(DIR)

  def get_json(self, url):
    response = self.requester.get_json(url)
    if response is None:
      return []
    return response

  def scrape(self):
    active = self.get_json(ACTIVE_URL)
    for item in active['puzzles']:
      id_ = item['id']
      filename = f"{DIR}/{item['print_date']}.json"
      # if exists(filename):
      #   log(f"Skipping {filename}, already saved.")
      #   continue
      clues = self.get_json(CLUES_URL.format(id_ = id_))
      stats = self.get_json(STATS_URL.format(id_ = id_))
      item['clues'] = clues
      item['stats'] = stats
      write(filename, json.dumps(item))
      log(f"Saved to {filename}")

if __name__ == '__main__':
  scraper = Scraper()
  scraper.setup()
  scraper.scrape()
  print(scraper.requester.cache_status())
