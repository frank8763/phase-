"""Calibrate complete mode-state suffix continuation without physical imports."""
import sys,json,hashlib,importlib.abc,time,signal,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1118_coupled_live_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','factory','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));from runtime import Engine,initial,python_replay,remaining_rows
import numpy as np

def main():
 assert not(O/'COMPLETION.json').exists();freeze=json.loads((O/'SOURCE_FREEZE.json').read_text());assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in freeze.items());guard=hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest();start=time.monotonic();cpp=0;py=0;maxerr=0.;rows=[];answer={'passed':False};engine=None
 def halt(*_):raise TimeoutError('BOUNDED120S_MODE_SEAM')
 signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,120)
 try:
  fixture=json.loads((R/'experiments/v1114_coupled_steering_mode/STATIC_T0_SOURCE_FIXTURE.json').read_text());engine=Engine(fixture['setup']);cuts=[0,2200,2320,2799,2800,5000,5120,5599,5600,5899,5900,8090]
  for sign,name in [(1,'negative_to_positive'),(-1,'positive_to_negative')]:
   schedule=[(0.,0.,2200,0),(-sign*.42722137342572125,0.,600,1),(0.,0.,2200,0),(sign*.42722137342572125,0.,600,1),(sign*.42722137342572125,.08,300,0),(0.,0.,2200,0)]
   origin=initial(fixture['packet']);ss,uu,mem,episodes,active=python_replay(fixture['setup'],origin,schedule);py+=len(uu)
   for cut in cuts:
    suffix=remaining_rows(schedule,cut);p=dict(state=ss[cut].copy(),last_ctrl=mem[cut,:4].copy(),integral=float(mem[cut,4]),coupled_episode=bool(episodes[cut]),steering_motion_active=bool(active[cut]));cs,cu=engine.simulate(p,suffix);ps,pu,*_=python_replay(fixture['setup'],p,suffix);py+=len(pu);error=max(float(abs(cs-ps).max()),float(abs(cu-pu).max()),float(abs(cs-ss[cut:]).max()),float(abs(cu-uu[cut:]).max()));maxerr=max(maxerr,error);assert error<=1e-8,'MODE_SUFFIX_CHANGED';rows.append({'direction':name,'offset':cut,'native':len(cu),'maximum_error':error})
   cut=2320;p=dict(state=ss[cut].copy(),last_ctrl=mem[cut,:4].copy(),integral=float(mem[cut,4]),coupled_episode=True,steering_motion_active=False)
   assert abs(ss[cut,3])>.003
   try:engine.simulate(p,remaining_rows(schedule,cut))
   except AssertionError as error:assert 'COMPLETE_SUFFIX_CONTRACT'in str(error)
   else:raise AssertionError('MISSING_ACTIVE_FLAG_NOT_DETECTED')
  p['steering_motion_active']=True;p['coupled_episode']=False
  try:engine.simulate(p,remaining_rows(schedule,2320))
  except AssertionError as error:assert 'ACTIVE_MODE_MISSING_EPISODE'in str(error)
  else:raise AssertionError('INCONSISTENT_MODE_ALLOWED')
  refused=[]
  for name in ['mujoco','physical','vehicle','factory','rclpy','torch']:
   try:__import__(name)
   except AssertionError:refused.append(name)
   else:raise AssertionError('PHYSICAL_IMPORT_ALLOWED')
  answer.update(passed=True,maximum_state_ctrl_error=maxerr,suffixes=rows,missing_active_refused=True,inconsistent_episode_refused=True,physical_imports_refused=refused)
 except BaseException as e:answer.update(error=repr(e),traceback=traceback.format_exc())
 finally:signal.setitimer(signal.ITIMER_REAL,0)
 answer.update(closed=True,cpp_native=engine.native if engine else 0,cpp_calls=engine.calls if engine else 0,python_native=py,models=0,physical_integrations=0,wall_s=time.monotonic()-start,guard_original=hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()==guard,source_unchanged=all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in freeze.items()),live_physical_integration_qualified=False,automatic_physical_launch=False);answer['passed']=bool(answer['passed']and answer['guard_original']and answer['source_unchanged']);(O/'COMPLETION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps({k:v for k,v in answer.items()if k!='suffixes'}))
if __name__=='__main__':main()
