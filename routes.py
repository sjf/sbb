import sys
import logging
import os
import json
from flask import Flask, render_template, request, flash, redirect, send_from_directory
from markupsafe import escape
from flask import Blueprint, current_app
import elasticsearch
from es import ElasticSearch
from http import HTTPStatus
import urllib.parse as ul

from pyutils import *
from gunicorn_util import *
from query import Query

bp = Blueprint('main', __name__)
es = ElasticSearch()

@bp.route('/search')
def search():
  query = Query(request.args)
  result = _search(query)
  # if result:
  return handle_result(query, result)
  # else:
  # pass
  # handle error

def _search(query):
  try:
    return es.search(query)
  except Exception as e:
    flash("Something went wrong")
    info = ''
    if isinstance(e, elasticsearch.BadRequestError):
      info = e.info
    access_log_error(f"Error handling search request: {info}", exc_info = e)
    if current_app.debug:
      raise e
    # In production swallow the exception and let the parent handle the error.
    return None

def handle_result(query, result):
  access_log_json('RESULTS', {
    'params': request.query_string.decode('utf-8'),
    'count': len(result.results),
    'urls': list(map(lambda x:x.url, result.results)),
    })
  # Canonical URL for results page is the first page of results.
  return render_template('results.html', result=result, canon_url=result.pagination.first)

if os.getenv('FLASK_ENV') == 'development':
  @bp.route('/', defaults={'filename': 'index.html'})
  @bp.route('/<path:filename>')
  def send_from_site_directory(filename):
    if exists('site/' + filename):
      return send_from_directory('site', filename, mimetype='text/html')
    return abort(404)

@bp.route('/health')
def health():
  return 'OK'

@bp.after_app_request
def add_header(response):
  response.headers['X-SBB'] = f'{maybe_read("build_time.txt", "n/a")} {maybe_read("git.txt", "n/a") }'
  return response
