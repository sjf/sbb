import pytest
import requests
import http.client
import os
import re
import pyutils
import random
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from pyutils import *
from testdata import *

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
  assert a.text == b.text, f'{url1} == {url2}'

def assert_in_order(response, l):
  assert_code(response, 200)
  t = response.text
  for s in l:
    assert s in t, t
  reg = joinl(l, sep='.*')
  assert re.search(reg, t, re.DOTALL), t

####### CUJs

def test_index():
  assert_contains(get(''), "Today's Spelling Bee")
  assert_contains(get('/'), "Today's Spelling Bee")

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

@pytest.mark.parametrize("url, title, clue, answer, hint1, hint2", [
  pytest.param('/puzzle/2024-12-31',
    "Spelling Bee from December 31, 2024", "Poker entry fee", "pentane",
    "A total of five words end with “ane”.", "Two words are borrowed from Italian.", marks=pytest.mark.live),
  pytest.param('/puzzle/2024-12-29',
    "Spelling Bee from December 29, 2024", "Hodge lodge", "olio",
    "Two words in this set end with “lio”.", "", marks=pytest.mark.testdata)
])
def test_puzzle(url, title, clue, answer, hint1, hint2):
  response = get(url)
  assert_contains(response, title)
  assert_contains(response, clue)
  assert_contains(response, answer)
  assert_contains(response, hint1)
  assert_contains(response, hint2)

def test_puzzle_latest():
  response = get('/puzzle/latest')
  assert_contains(response, "NYT Spelling Bee")

def test_clues():
  response = get('/clues/d')
  assert_contains(response, "starting with ‘D’")

@pytest.mark.parametrize("query, dest, clue, answer", [
  pytest.param('cathode', "/clue/rabbit-ears-on-a-cathode-tube-tv", "Rabbit ears on a cathode tube tv",
    "antenna", marks=pytest.mark.live),
  pytest.param(T1_A, U1_A, T1_A, W1_A, marks=pytest.mark.testdata)
])
def test_search(query, dest, clue, answer):
  response = get(f'/search?q={query}')
  assert_contains(response, dest)
  assert_contains(response, clue)
  assert_contains(response, answer)

@pytest.mark.skipif(os.environ.get('GITHUB_RUN_ID', False), reason='Skipping on GH action')
# It's too difficult to get all the parts to agree where the logs dir is on GH.
def test_signup():
  email = f'test-{random.randint(1000,9999)}@example.com'
  response = post(f'/thank-you', {'email':email})
  assert_contains(response, 'Thank you')
  assert not 'Sign up' in response.text
  assert email in read(joinp(get_log_dir(), config['EMAIL_FILE']))

def test_js():
  for url in ['/', '/search?q=cathode']:
    soup = BeautifulSoup(get(url).text, 'html.parser')
    js_files = [script['src'] for script in soup.find_all('script', src=True)]
    js_files = filter(lambda x:x.startswith('/'), js_files)
    for js in js_files:
      assert_code(get(js), 200)

####### Tests for content of generated pages #####

def test_backend_css():
  for url in ['/', '/search?q=cathode']:
    soup = BeautifulSoup(get(url).text, 'html.parser')
    css_files = [link['href'] for link in soup.find_all('link', rel="stylesheet")]
    css_files = filter(lambda x:x.startswith('/'), css_files)
    for cs in css_files:
      assert_code(get(cs), 200)

@pytest.mark.testdata
def test_search_results_duplicate_clues_latest_only():
  r = get(f'/search?q=go')
  assert_in_order(r, ['December 31, 2024', 'December 30, 2024', 'December 29, 2024', 'December 31, 2024'])
  assert_in_order(r, ['Go cold turkey', 'Go cold turkey', 'Go cold turkey!!!!!',
    'Want an expensive ticket and possibly be towed'])
  assert_in_order(r, ['/clue/go-cold-turkey', '/clue/go-cold-turkey', '/clue/go-cold-turkey',
    'clue/want-an-expensive-ticket-and-possibly-be-towed-go-park-next-to-a-fire'])

@pytest.mark.parametrize('q', ['hydrant', 'tadhnry', 'A D H N R Y T'])
@pytest.mark.testdata
def test_search_by_puzzle_letters(q):
  r = get(f'/search?q={q}')
  assert 'December 31, 2024' in r.text
  assert 'A D H N R Y' in r.text

@pytest.mark.parametrize('q', ['31 December', 'December 31', 'December 31, 2024', '31 December, 2024'])
@pytest.mark.testdata
def test_search_by_puzzle_date(q):
  r = get(f'/search?q={q}')
  assert 'December 31, 2024' in r.text
  assert 'A D H N R Y' in r.text

@pytest.mark.testdata
def test_search_month_does_not_match_puzzle_date():
  r = get('/search?q=December')
  assert_in_order(r, ['Holiday in December','December 31, 2024'])
  assert 'A D H N R Y' not in r.text

@pytest.mark.testdata
def test_td_clue_page():
  r = get('/clue/go-cold-turkey')
  assert_in_order(r, ['puzzle-3-word-for-detox', 'puzzle-2-word-for-detox', 'detox'])
  assert_in_order(r, ['Go cold turkey', 'Go cold turkey!!!!!', 'Go cold turkey'])
  assert_in_order(r, ['December 30, 2024', 'December 29, 2024', 'December 24, 2024'])
  assert 'Detoxification from an intoxicating or addictive substance' in r.text

@pytest.mark.testdata
def test_td_clue_archive():
  r = get('/clues/')
  assert_in_order(r, ['1 clues', '2 clues', '4 clues'])
  assert_in_order(r, ['/clues/a/1', '/clues/d/1', '/clues/g/1'])

@pytest.mark.testdata
@pytest.mark.parametrize(
    "url", ['/puzzles/latest', '/puzzles/2024/12', '/puzzles/']
)
def test_td_puzzle_archive(url):
  r = get(url)
  assert_in_order(r, ['December 24, 2024', 'December 29, 2024', 'December 30, 2024'])
  assert_in_order(r, ['T E F O U X', 'B G I M O R', 'D H I L N O'])

####### Other pages
def test_redirects_clue():
  assert_same('/clue/', '/clues')
  assert_same('/clue',  '/clues')

def test_redirects_clues():
  assert_same('/clues/', '/clues')

  assert_same('/clues/d',  '/clues/d/1')
  assert_same('/clues/d/', '/clues/d/1')

@pytest.mark.live
def test_redirects_other_clue_indexes():
  assert_same('/clues/0-9',   '/clues/0-9/1')
  assert_same('/clues/0-9/',  '/clues/0-9/1')
  assert_same('/clues/symbols',  '/clues/symbols/1')

def test_redirects_puzzle():
  assert_same('/puzzle',  '/puzzle/latest')
  assert_same('/puzzle/', '/puzzle/latest')

def test_redirects_puzzles():
  assert_same('/puzzles',  '/puzzles/latest')
  assert_same('/puzzles/', '/puzzles/latest')

def test_no_redirects():
  assert_code(get('/clues/does-not-exist'), 404)
  assert_code(get('/clues/ab/c'), 404)
  assert_code(get('/puzzles/abc'), 404)
  assert_code(get('/puzzle/abc'), 404)

def test_internal_pages():
  assert_code(get('/err/500.html'), 404)

def test_sitemap():
  response = get('/sitemap.xml')
  assert '/definition/' not in response.text

####### Test internal pages

def test_health():
  response = get('/health')
  assert_contains(response, 'OK')

@pytest.mark.parametrize('url', ['/admin/index.html', '/admin/emails.csv', '/admin/does-not-exist.txt'])
def test_admin(url):
  r = get(url)
  assert_code(r, 405)

@pytest.mark.parametrize('url', ['/admin/login', '/admin/logout'])
def test_admin_login(url):
  r = get(url)
  assert_contains(r, 'Password')
