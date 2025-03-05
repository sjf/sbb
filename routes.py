import sys
import logging
import os
import json
import elasticsearch
import fcntl
import mimetypes
from flask import Flask, render_template, request, flash, redirect, send_from_directory, Blueprint, current_app, abort, session
from markupsafe import escape
from http import HTTPStatus

from pyutils import *
from pyutils.settings import config
from gunicorn_util import *
from site_util import http_error_messages
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

@bp.route('/thank-you', methods=['GET', 'POST'])
def thankyou():
  if request.method == 'GET':
      return redirect('/')
  email = request.form.get('email')
  access_log(f'EMAIL SUBMITTED: "{email}"')

  ts = timestamp()
  user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
  line = f'{ts},{user_ip},{email}\n'

  file = joinp(get_log_dir(), config['EMAIL_FILE'])
  with open(file, 'a') as fh:
      fcntl.flock(fh, fcntl.LOCK_EX)  # Lock the file
      fh.write(line)
      fcntl.flock(fh, fcntl.LOCK_UN)  # Unlock after writing

  url='/thank-you'
  return render_template('thank_you.html', url=url, canon_url=url)

if os.getenv('FLASK_ENV') == 'development':
  @bp.route('/', defaults={'filename': 'index.html'})
  @bp.route('/<path:filename>')
  def send_from_serving_directory(filename):
    SERVING_DEST = config['SERVING_DEST']
    if exists(joinp(SERVING_DEST, filename)):
      return send_from_directory(SERVING_DEST, filename, mimetype='text/html')
    return abort(404)

@bp.route('/admin/login', methods=['GET', 'POST'])
def login():
  if session.get("authenticated", False):
    return redirect('/admin/index.html')
  mesg = ""
  if request.method == 'POST':
    if request.form.get('password') == read(config['ADMIN_PASSWORD_FILE']):
      session['authenticated'] = True
      return redirect('/admin/index.html')
    else:
      mesg = "Login failed"
  return render_template('login.html', mesg=mesg)

@bp.route('/admin/logout')
def logout():
  session.pop('authenticated', None)
  return redirect('/admin/login')

@bp.route('/admin/index.html')
def admin():
  if not session.get("authenticated", False):
    return redirect('/admin/login')
  dir = config['ADMIN_FILES_DIR']
  files = os.listdir(dir)
  files = filter(lambda f:is_file(joinp(dir,f)), files)
  files = sorted(files)
  return render_template('files.html', files=files)

@bp.route('/admin/<path:filename>')
def serve_admin_files(filename):
  if not session.get("authenticated", False):
    return redirect('/admin/login')
  mimetype, _ = mimetypes.guess_type(filename)
  if mimetype is None:
    mimetype = "text/plain"
  return send_from_directory(config['ADMIN_FILES_DIR'], filename, mimetype=mimetype)

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
