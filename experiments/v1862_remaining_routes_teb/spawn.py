"""Shared actual process creation seam: inherited readonly task-local stdin."""
import subprocess
from pathlib import Path

def spawn(argv,*,cwd,empty_stdin):
 p=Path(empty_stdin)
 assert p.is_file()and not p.is_symlink()and p.stat().st_size==0,'READONLY_EMPTY_STDIN_IDENTITY'
 with p.open('rb')as stream:
  return subprocess.Popen(argv,cwd=cwd,stdin=stream,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
