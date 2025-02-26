import os
import subprocess
import sys
import time, datetime
import humanfriendly
import logging
import configparser
import traceback
import re
import ast
from collections import Counter, defaultdict
from pathlib import Path

# ISO date format.
ISO_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
ACCESS_LOG_DATE_FORMAT = '%d/%b/%Y:%H:%M:%S %z'

def timestamp(access_log=True):
  fmt = ACCESS_LOG_DATE_FORMAT if access_log else ISO_DATE_FORMAT
  return datetime.datetime.now().astimezone().strftime(fmt)

def duration(start, end):
  return humanfriendly.format_timespan(end - start)

list_handler = None
logger = logging.getLogger('pyutils')
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s',  datefmt=ISO_DATE_FORMAT)
is_initialized = False

def _setup_logging(list_handler=False):
  logger.setLevel(logging.DEBUG)

  # console handler
  console_handler = logging.StreamHandler()

  log_dir = os.environ.get('PYUTILS_LOG_DIR', f'{Path.home()}/log/')
  if not os.path.isdir(log_dir):
    log_warn(f'Creating log file directory {log_dir}')
    os.makedirs(log_dir, exist_ok=True)
  log_file = os.environ.get('PYUTILS_LOG_FILE', 'pyutils.log')

  # file handler
  file_handler = logging.FileHandler(f'{log_dir}/{log_file}')

  handlers = [console_handler, file_handler]
  if list_handler:
    # list handler
    list_handler = ListHandler()
    handlers.append(list_handler)

  for handler in handlers:
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

  console_handler.setLevel(logging.INFO)
  is_initialized = True

def get_logged_messages():
  if not list_handler:
    return []
  return list_handler.messages

class ListHandler(logging.Handler):
  """ A logging handler that stores log messages in memory. """
  def __init__(self):
    super().__init__()
    self.messages = []
  def emit(self, record):
    self.messages.append(self.format(record))

def log(message, ex=None):
  if ex:
    logger.info(format_ex(ex))
  logger.info(message)

def log_warn(message, ex=None):
  if ex:
    logger.warn(format_ex(ex))
  logger.warning(message)

def log_error(message, ex=None):
  if ex:
    logger.error(format_ex(ex))
  logger.error(message)

def log_fatal(message, ex=None):
  log_error(message, ex)
  sys.exit(1)

def log_debug(message, ex=None):
  if ex:
    logger.debug(format_ex(ex))
  logger.debug(message)

def catch_and_log_exceptions(func):
  def wrapper(*args, **kwargs):
    """ Returns True if func failed. Otherwise return the result of the function (which should be True if failed.)"""
    try:
      res = func(*args, **kwargs)
      if res in (True, False):
        return res
      return False # did not fail.
    except Exception as ex:
      log("catch_and_log_exceptions", ex)
      return True # failed.
  return wrapper

def format_ex(ex):
  exc_type, exc_value, exc_traceback = sys.exc_info()
  return ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

def print_res(func):
  def wrapper(*args, **kwargs):
    res = func(*args, **kwargs)
    print(res)
    return res
  return wrapper

if not is_initialized:
  _setup_logging()

