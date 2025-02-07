import logging
import json
from flask import has_request_context, request
from pyutils import *

def client_ip():
  if has_request_context():
    return request.headers.get('X-Real-IP', request.remote_addr)
  else:
    return '-'

def access_log(mesg):
  """ Logs an info message to the gunicorn access log."""
  log_mesg = f"{client_ip()} - - [{timestamp()}] {mesg}"

  logger = logging.getLogger("gunicorn.access")
  logger.info(log_mesg)

def access_log_json(tag, obj):
  """ Logs a json info message to the gunicorn access log."""
  access_log(f"LOG_JSON {tag} {json.dumps(obj)}")

def access_log_error(mesg, level=logging.ERROR, exc_info = None):
  """ Logs to the gunicorn error log with an optional stack trace."""
  log_mesg = f'{client_ip()} {mesg}'
  logger = logging.getLogger("gunicorn.error")
  logger.log(level, log_mesg, exc_info = exc_info)
