import pprint
from mbutils import *

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
