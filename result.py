import re
import json
import os
from typing import List, Any, Dict, Optional
from flask import request

from pyutils import *
from pyutils.settings import config
from query import Query
from model import PaginateByNum, GSearchResult

class Result():
  def __init__(self, query: Query, results: List[GSearchResult], has_next: bool):
    self.term = query.term
    self.results = results
    base_url = remove_url_param(request.url, 'page')
    self.pagination = PaginateByNum(current=query.page_num, has_next=has_next, base_url=base_url)

  def __repr__(self) -> str:
    dict_ = filterd(lambda k,v:not k.startswith('__'), self.__dict__)
    return f'<Result {dict_}>'
