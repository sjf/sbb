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
config = settings.load_config(TEST_SETTINGS)
print(dictl(config))

###### Test utils
BACKEND = re.sub('/$','', config['BACKEND']) # remove tailing slash from backend.
HEADERS = {'User-Agent': f"pytest-python-requests/{requests.__version__}"}
TIMEOUT = config['PYTEST_TIMEOUT']
VERIFY_SSL = config['VERIFY_SSL']
def get(path, params={}, auth=None):
  url = BACKEND + path
  response = requests.get(url, params, timeout=TIMEOUT, verify=VERIFY_SSL, auth=auth, headers=HEADERS, allow_redirects=False)
  print(f"\nGET {response.url}")
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

def assert_results_same(expected_response, response):
  assert response.status_code == expected_response.status_code

  expected_results = get_results(expected_response)
  results = get_results(response)
  assert results == expected_results

def get_results(response):
  soup = BeautifulSoup(response.text, 'html.parser')
  return soup.find_all('div', class_='book')

####### CUJs

def test_index():
  response = get('/')
  assert_contains(response, "Today's NYT Spelling Bee")

def test_index_http_redirect():
  if config['IS_FLASK'] or config['IS_GUNICORN'] or BACKEND.startswith('http://'):
    # Flask and gunicorn don't listen on both ports.
    # Testing only with http means https is not available.
    pytest.skip(f"Skipping http->https redirect test for backend:{BACKEND}")
  https_url = BACKEND + '/test?foo=bar'
  http_url = https_url.replace('https://', 'http://', 1)
  response = requests.get(http_url, timeout=TIMEOUT, allow_redirects=False, headers=HEADERS)
  redirect_url = response.headers.get('Location')

  assert_code(response, 301)
  assert redirect_url == https_url

def test_index_invalid_param_ignored():
  response = get('/', params={'foo': 'bar'})
  response2 = get('/')
  assert_contains(response, "Today's NYT Spelling Bee")
  assert response.text == response2.text

def test_puzzles():
  response = get('/puzzles/latest')
  assert_contains(response, "NYT Spelling Bee")

def test_puzzle():
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
  version = settings.config['VERSION']
  response = get(f'/static/style.{version}.css')
  assert_contains(response, '')

def test_js():
  version = settings.config['VERSION']
  response = get(f'/static/script.{version}.min.js')
  assert_contains(response, '')

####### Other pages

def test_health():
  response = get('/health')
  assert_contains(response, 'OK')
