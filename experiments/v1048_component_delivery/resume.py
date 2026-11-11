"""Fail-safe resume only a registered paused relay parent, no work launch."""
import os,signal,sys,time
from pathlib import Path
time.sleep(150);pid=int(sys.argv[1]);start=sys.argv[2]
try:
 row=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
 if row[19]==start and row[0]=='T':os.kill(pid,signal.SIGCONT)
except ProcessLookupError:pass
except FileNotFoundError:pass
