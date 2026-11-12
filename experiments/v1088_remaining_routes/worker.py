"""Unchanged successful worker with public t0 metadata selected by task case."""
import sys, types
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1085_pose_entry_relay'))
import worker_relay
ORIGINAL=worker_relay.ORIGINAL
OLD="O/'NORTH_SOUTH_T0_METADATA.json'"
NEW="O/(task['case_id']+'_T0_METADATA.json')"
def patched_source():
 s=worker_relay.patched_source();assert s.count(OLD)==1
 p=s.replace(OLD,NEW);assert p.replace(NEW,OLD)==s
 return p
def load_worker():
 m=types.ModuleType('remaining_routes_same_science_worker');m.__file__=str(ORIGINAL)
 exec(compile(patched_source(),str(ORIGINAL),'exec'),m.__dict__);return m
if __name__=='__main__':
 exec(compile(patched_source(),str(ORIGINAL),'exec'),dict(__name__='__main__',__file__=str(ORIGINAL)))
