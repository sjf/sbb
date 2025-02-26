import pytest
import requests
import http.client
import os
import re
import pyutils
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from pyutils import *

# These can be overridden by setting the env var.
TEST_SETTINGS = {
  'BACKEND': 'https://localhost',
  'IS_FLASK': False,
  'IS_GUNICORN': False,
  'PYTEST_TIMEOUT': 2,
  'VERIFY_SSL': True
}
config = load_config(TEST_SETTINGS)
print(dictl(config))

###### Test utils
BACKEND = re.sub('/$','', config['BACKEND']) # remove tailing slash from backend.
HEADERS = {'User-Agent': f"pytest-python-requests/{requests.__version__}"}
TIMEOUT = config['PYTEST_TIMEOUT']
VERIFY_SSL = config['VERIFY_SSL']
def get(path, params={}, auth=None):
  url = BACKEND + path
  print(f"\nGET {url}")
  response = requests.get(url, params, timeout=TIMEOUT, verify=VERIFY_SSL, auth=auth, headers=HEADERS, allow_redirects=True)
  return response

def post(path, body):
  url = BACKEND + path
  response = requests.post(url, data=body, timeout=TIMEOUT, verify=VERIFY_SSL, allow_redirects=False, headers=HEADERS)
  print(f"\nPOST {response.url}")
  if response.status_code == 301:
    redirect_url = response.headers.get('Location')
    # Strictly you should only do a GET on a redirect URL.
    response = requests.post(redirect_url, data=body, timeout=TIMEOUT, verify=VERIFY_SSL, allow_redirects=False, headers=HEADERS)
    print(f"\nPOST {response.url}")
  return response

def assert_code(response, expected_code):
  code = response.status_code
  print(f"RESP {code} {http.client.responses[code]}")
  assert response.status_code == expected_code, f"Wanted HTTP response code {expected_code}, Got {code} {http.client.responses[code]}\n{dictl(response.headers)}\n\n{response.text}"

def assert_contains(response, text):
  assert_code(response, 200)
  assert text in response.text, f"Wanted '{text}'. Got:\n{dictl(response.headers)}\n\n{response.text}"

def assert_same(url1, url2):
  a = get(url1)
  b = get(url2)
  assert_code(a, 200)
  assert_code(b, 200)
  assert a.text == b.text

####### CUJs

def test_index():
  response = get('/')
  assert_contains(response, "Today's Spelling Bee")

def test_index_http_redirect():
  if config['IS_FLASK'] or config['IS_GUNICORN'] or BACKEND.startswith('http://'):
    # Flask and gunicorn don't listen on both ports.
    # Testing only with http means https is not available.
    pytest.skip(f"Skipping http->https redirect test for dev backend:{BACKEND}")
  https_url = BACKEND + '/test?foo=bar'
  http_url = https_url.replace('https://', 'http://', 1)
  response = requests.get(http_url, timeout=TIMEOUT, allow_redirects=False, headers=HEADERS)
  redirect_url = response.headers.get('Location')

  assert_code(response, 301)
  assert redirect_url == https_url

def test_index_invalid_param_ignored():
  response = get('/', params={'foo': 'bar'})
  response2 = get('/')
  assert_contains(response, "Today's Spelling Bee")
  assert response.text == response2.text

def test_puzzles():
  response = get('/puzzles/latest')
  assert_contains(response, "NYT Spelling Bee")

def test_puzzle():
  response = get('/puzzle/2024-12-31')
  assert_contains(response, "Spelling Bee from December 31, 2024")
  assert_contains(response, "Poker entry fee")
  assert_contains(response, "pentane")
  assert_contains(response, "ive words")
  assert_contains(response, "Italian")

def test_puzzle_latest():
  response = get('/puzzle/latest')
  assert_contains(response, "NYT Spelling Bee")

def test_clues():
  response = get('/clues/b')
  assert_contains(response, "NYT Spelling Bee")

def test_search():
  response = get('/search?q=cathode')
  assert_contains(response, "/clue/rabbit-ears-on-a-cathode-tube-tv")
  assert_contains(response, "Rabbit ears on a cathode tube tv")
  assert_contains(response, "antenna")

def test_css():
  for url in ['/', '/search?q=cathode']:
    soup = BeautifulSoup(get(url).text, 'html.parser')
    css_files = [link['href'] for link in soup.find_all('link', rel="stylesheet")]
    css_files = filter(lambda x:x.startswith('/'), css_files)
    for cs in css_files:
      assert_code(get(cs), 200)

def test_js():
  for url in ['/', '/search?q=cathode']:
    soup = BeautifulSoup(get(url).text, 'html.parser')
    js_files = [script['src'] for script in soup.find_all('script', src=True)]
    js_files = filter(lambda x:x.startswith('/'), js_files)
    for js in js_files:
      assert_code(get(js), 200)

####### Other pages
def test_redirects_clue():
  assert_same('/clue/', '/clues')
  assert_same('/clue',  '/clues')

def test_redirects_clues():
  assert_same('/clues/', '/clues')

  assert_same('/clues/d',  '/clues/d/1')
  assert_same('/clues/d/', '/clues/d/1')

def test_redirects_puzzle():
  assert_same('/puzzle',  '/puzzle/latest')
  assert_same('/puzzle/', '/puzzle/latest')

def test_redirects_puzzles():
  assert_same('/puzzles',  '/puzzles/latest')
  assert_same('/puzzles/', '/puzzles/latest')

def test_no_redirects():
  assert_code(get('/clues/abc'), 404)
  assert_code(get('/clues/ab/c'), 404)
  assert_code(get('/puzzles/abc'), 404)
  assert_code(get('/puzzle/abc'), 404)

def test_internal_pages():
  assert_code(get('/err/500.html'), 404)

def test_sitemap():
  response = get('/sitemap.xml')
  assert '/definition/' not in response.text

####### Test URL redirects


def test_health():
  response = get('/health')
  assert_contains(response, 'OK')
