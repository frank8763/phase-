"""New overnight authority, Phase-only resources, no model initialization."""
import sys,os,time,json,hashlib,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1148_overnight_causal_recovery'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
RESOURCE=apply()
sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'))
from result_io import dump,encode
GUARD_SHA='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def remaining():
 w=json.loads((O/'ROUND_WINDOW.json').read_text());assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'BOOT_CHANGED'
 return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def source_ok():return all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items())
def pin():
 for p in Path('/proc/self/task').iterdir():
  try:os.sched_setaffinity(int(p.name),{2});os.sched_setscheduler(int(p.name),os.SCHED_IDLE,os.sched_param(0))
  except ProcessLookupError:pass
def used():
 total=0
 for root in [O,R/'runs/v858_nav2_verified/v1148']:
  if root.exists():
   for p in root.rglob('*'):
    if p.is_file()and not p.is_symlink():total+=p.stat().st_size
 return total
