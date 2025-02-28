import pprint
from pyutils import *

def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, (dict, list, tuple)) or isinstance(right, (dict, list, tuple)):
        left_str = pprint.pformat(left, indent=2).splitlines()
        right_str = pprint.pformat(right, indent=2).splitlines()
        return [
            f"Assertion failed: {op}",
            "Left:",
            *left_str,
            "Right:",
            *right_str
        ]

def pytest_configure(config):
  if 'BACKEND' in os.environ:
    print("\nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print(f"Testing BACKEND:{os.environ['BACKEND']}")
    print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

def pytest_collection_modifyitems(items, config):
  for item in items:
    if not any(item.iter_markers()):
      item.add_marker("unmarked")
