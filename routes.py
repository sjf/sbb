import sys
import logging
import os
import json
import elasticsearch
from flask import Flask, render_template, request, flash, redirect, send_from_directory, Blueprint, current_app
from markupsafe import escape
from http import HTTPStatus

from pyutils import *
from pyutils.settings import config
from gunicorn_util import *
from jinja_util import http_error_messages
from es import ElasticSearch
from query import Query

bp = Blueprint('main', __name__)
es = ElasticSearch()

@bp.route('/search')
def search():
  query = Query(request.args)
  result = es.search(query)
  return handle_result(query, result)

def handle_result(query, result):
  access_log_json('RESULTS', {
    'params': request.query_string.decode('utf-8'),
    'count': len(result.results),
    'urls': list(map(lambda x:x.url, result.results)),
    })
  # Canonical URL for results page is the first page of results.
  return render_template('results.html', url=request.url, canon_url=result.pagination.first, result=result)

if os.getenv('FLASK_ENV') == 'development':
  @bp.route('/', defaults={'filename': 'index.html'})
  @bp.route('/<path:filename>')
  def send_from_serving_directory(filename):
    SERVING_DEST = config['SERVING_DEST']
    if exists(joinp(SERVING_DEST, filename)):
      return send_from_directory(SERVING_DEST, filename, mimetype='text/html')
    return abort(404)

@bp.route('/health')
def health():
  return 'OK'

@bp.after_app_request
def add_header(response):
  response.headers['X-SBB'] = f'{maybe_read("build_time.txt", "n/a")} {maybe_read("git.txt", "n/a") }'
  return response

@bp.errorhandler(Exception)
def error_handler(error):
  code = getattr(error, "code", 500)
  log_error(f'Exception caught by routes.error_handler, returning code:{code}', error)
  message = http_error_messages[code]
  status = HTTPStatus(code).phrase
  return render_template("internal/error.html", url=f'/error/{code}', code=code, message=message, status=status), code
