import re
import json
import os
from typing import List, Any, Dict, Optional
from flask import request

from pyutils import *
from pyutils.settings import config
from query import Query

class Result():
  def __init__(self, query: Query, results = []):
    self.term = query.term
    self.results = results
    # The page nums are strings bc None type is rendered by jinja as 'None'
    self.next_page = ''
    self.prev_page = ''
    self.at_max = False

    if results:
      # Only show prev/next buttons if there are results.
      # Page num is provided by the user so it can be any number.
      self.at_max = query.page_num >= config['MAX_PAGE_NUM']
      if len(results) > config['PAGE_SIZE'] and not self.at_max:
        # There are more results, remove the extra one.
        results = results[:config['PAGE_SIZE']]
        self.next_page = replace_url_param(request.url, 'page', query.page_num + 1)
      # Only show the back link if there are results.
      if query.page_num > 0:
        self.prev_page = replace_url_param(request.url, 'page', query.page_num - 1)

  @property
  def first_page(self):
    return remove_url_param(request.url, 'page')


  def __repr__(self):
    dict_ = filterd(lambda k,v:not k.startswith('__'), self.__dict__)
    return f'<Result {dict_}>'
