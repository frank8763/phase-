"""Bounded OS-only sleep inhibition with the exact registered process entrypoint."""
import argparse,json,time
from pathlib import Path
def identity(pid):
 try:
  proc=Path('/proc')/str(pid);stat=(proc/'stat').read_text().rsplit(') ',1)[1].split();args=(proc/'cmdline').read_bytes().split(b'\0')
  return dict(state=stat[0],start_ticks=stat[19],argv=[a.decode()for a in args if a])
 except FileNotFoundError:return None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pid',type=int,required=True);ap.add_argument('--entrypoint',required=True);ap.add_argument('--deadline',type=float,required=True);ap.add_argument('--probe-only',action='store_true');a=ap.parse_args()
 initial=identity(a.pid);assert initial is not None and initial['state']!='Z'and a.entrypoint in initial['argv'],'REGISTERED_PHASE_PROCESS_IDENTITY_REQUIRED'
 assert Path(a.entrypoint).resolve().is_relative_to(Path(__file__).resolve().parents[2]/'experiments')
 assert time.time()<a.deadline,'ABSOLUTE_OS_DEADLINE_EXPIRED'
 print(json.dumps(dict(status='INHIBITOR_IDENTITY_VERIFIED',pid=a.pid,entrypoint=a.entrypoint,start_ticks=initial['start_ticks'],deadline=a.deadline,models=0,integrations=0)),flush=True)
 if a.probe_only:return
 while time.time()<a.deadline:
  current=identity(a.pid)
  if current is None or current['state']=='Z'or current['start_ticks']!=initial['start_ticks']or current['argv']!=initial['argv']:break
  time.sleep(min(15,max(0,a.deadline-time.time())))
 print(json.dumps(dict(status='INHIBITOR_RELEASED',models=0,integrations=0)),flush=True)
if __name__=='__main__':main()
