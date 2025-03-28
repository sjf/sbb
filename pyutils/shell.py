import os
import subprocess
import sys
import glob
import shutil

from .log import log, log_fatal

#### Shell, IO and Filesystem Utils ###

def shell(cmd, env=None, verbose=True, with_output=False):
  if verbose:
    log(f"Running '{cmd}'")
  kwargs = {
    'shell': True,
    'check': True, # check=True is equivalent of set -e, fail the script if this command fails.
    'capture_output': with_output,
    'text': True, # output as text, as opposed to bytes.
  }
  if env:
    kwargs['env'] = env
  result = subprocess.run(cmd, **kwargs)
  return result.stdout

def read(f, binary=False):
  mode = 'rb' if binary else 'r'
  if not f:
    raise Exception("Missing file name.")
  with open(f, mode) as fh:
    return fh.read().strip()

def read_value(f):
  """ Read a non-empty value from a file."""
  value = read(f)
  if not value:
    raise Exception(f"File '{f}' was empty")
  return value

def maybe_read(f, default=''):
  """ Returns the contents of file `f`, or `default` if the file does not exist."""
  try:
    return read_value(f)
  except FileNotFoundError:
    return default

def read_lines(f, to_list=True):
  if not f:
    raise Exception("Missing file name.")
  with open(f) as fh:
    result = map(lambda x:x.rstrip(), fh.readlines())
    if to_list:
      return list(result)
    return result

def write(f, s, create_dirs=False, binary=False):
  if not f:
    raise Exception("Missing file name.")
  try:
    if create_dirs:
      dirs = os.path.dirname(f)
      if dirs:
        mkdir(dirs)
    mode = 'wb' if binary else 'w'
    with open(f, mode) as fh:
      fh.write(s)
  except Exception as e:
    raise Exception(f"Failed to write to '{f}'") from e

def append(f, s):
  try:
    with open(f, 'a') as fh:
      fh.write(s)
  except Exception as e:
    raise Exception(f"Failed to append to '{f}'") from e

def touch(f):
  write(f, '')

def rm(f):
  try:
    os.remove(f)
  except FileNotFoundError:
    pass

def rm_glob(pattern, verbose=False):
  arg = '-v' if verbose else ''
  subprocess.run(f"rm {arg} {pattern} 2>/dev/null", shell=True, check=False)

def mkdir(d):
  os.makedirs(d, exist_ok=True)
  # log(f"Created dirs {d}")

def exists(f):
  return f and os.path.exists(f)

def exists_dir(f):
  return f and os.path.isdir(f)

is_dir = exists_dir

def is_file(f):
  return f and os.path.isfile(f)

def mv(a: str, b: str) -> None:
  if b[-1] == '/' or exists_dir(b):
    # destination is a directory.
    b = b + basename(a)
  os.rename(a,b)

def rm_rf(path, verbose=False):
  if not exists(path):
    return
  vflag = "-v" if verbose else ""
  shell(f'rm -rf {vflag} {path}')

def cp(a: str, b: str, verbose: bool=False) -> None:
  if verbose:
    log(f"Copying '{a}' -> '{b}'")
  shutil.copy(a, b)

def ln(src: str, dest: str, target_is_directory: bool = False) -> None:
  if os.path.islink(dest):
    os.unlink(dest)
  os.symlink(src, dest, target_is_directory=target_is_directory)

def get_size(f):
  """ Returns the file size of `f` in human-readable format."""
  if not exists(f):
    return 0
  return subprocess.getoutput(f"du -hs {f} | cut -f1")

def ls(pattern):
  return glob.glob(pattern)

def stderr(s):
  sys.stderr.write(f"{str(s)}\n")

def basename(path: str) -> str:
  return os.path.basename(path)
def dirname(path: str) -> str:
  return os.path.dirname(path)
def realpath(path: str) -> str:
  return os.path.abspath(path)

def joinp(a: str, b: str) -> str:
  if not a:
    return b
  if not b:
    return a
  if a[-1] != '/' and b[0] != '/':
    return a + '/' + b
  if a[-1] == '/' and b[0] == '/':
    return a[:-1] + b
  return a + b
