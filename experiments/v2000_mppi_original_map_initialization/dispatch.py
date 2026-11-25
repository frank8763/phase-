"""Launch two actual algorithm qualifiers concurrently on different physical cores."""
from common import R,C,ROOT,read,put,sha,LANES
import os,subprocess,time,traceback

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(ROOT/'DISPATCH_ONCE.json').exists();assert read(ROOT/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];assert read(R/'runs/v1983_rpp_bounded_console_queue/CAMPAIGN_RESULT.json')['closed']and read(R/'runs/v1983_rpp_bounded_console_queue/rounds/common_02__RPP/POST_ROUND_STORAGE_BARRIER.json')['passed']
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);reserve=(16+32+32+512)*1024**2;assert used+reserve<15*1024**3,'PARALLEL_2LANE_AGGREGATE_STORAGE_PEAK';before=__import__('json').dumps([x for x in read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')['slots']if x['method']=='MPPI'],sort_keys=True);put(ROOT/'DISPATCH_ONCE.json',dict(pid=os.getpid(),unix=time.time(),maximum_wall_s=360,lanes=LANES,allruns_bytes=used,aggregate_reserved_peak=used+reserve,physical_models_authorized=False));jobs=[];result=dict(closed=False,passed=False,formal_common_tasks=0,physics_native=0,replay_native=0,first_error=None)
 try:
  for lane,cpu in LANES.items():
   out=ROOT/'lanes'/lane;assert not(out/'OWNER_ONCE.json').exists()and not(out/'OWNED_CHILD.json').exists()and not(out/'COMPLETION.json').exists();log=(out/'owner.console').open('xb');env=dict(os.environ,PHASE_ALGORITHM_LANE=lane,PYTHONDONTWRITEBYTECODE='1');p=subprocess.Popen(['taskset','-c',str(cpu),'/usr/bin/python3','-B',str(C/'owner.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT);jobs.append((lane,p,log));put(ROOT/'DISPATCH_PROGRESS.json',dict(lanes_started=[dict(lane=n,pid=p.pid)for n,p,_ in jobs],unix=time.time()))
  for lane,p,log in jobs:p.wait(timeout=330);log.close()
  result['lanes']={lane:read(ROOT/'lanes'/lane/'COMPLETION.json')for lane in LANES};result['passed']=all(v['passed']for v in result['lanes'].values());assert __import__('json').dumps([x for x in read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')['slots']if x['method']=='MPPI'],sort_keys=True)==before,'MPPI_FORMAL_SLOTS_CHANGED_BY_MATH_ONLY'
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  for _,p,log in jobs:
   if p.poll()is None:p.terminate();p.wait(timeout=10)
   log.close()
  result['closed']=True;put(ROOT/'PARALLEL_RESULT.json',result)
 print(__import__('json').dumps(dict(passed=result['passed'],closed=True,lanes={k:dict(passed=v['passed'],first_error=v.get('first_error')or(v.get('native_result')or{}).get('first_error'))for k,v in result.get('lanes',{}).items()})));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
