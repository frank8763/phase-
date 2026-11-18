"""Saved static-valid source on coupled domain, exact original-state waits."""
import sys,json,time,signal,hashlib,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];JOB=json.loads(Path(sys.argv[1]).read_text());O=Path(JOB['output'])
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(C));from geometry import Geometry
from source import Engine,initial,python_replay,COUNTS
from recovery_source import forecast_packet
import numpy as np

def main():
 assert hashlib.sha256(Path(JOB['table']).read_bytes()).hexdigest()==JOB['table_sha256'],'CAUSAL_TABLE_SHA_CHANGED'
 start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('PHASE600')));signal.alarm(600);x=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());x['safe_terminal_pose']=json.loads((R/'runs/v1125_safe_goal_region/TERMINAL_SELECTION.json').read_text())['selected_body_pose'];rows=json.loads((R/'runs/v1133_terminal_spatial_corridor/TERMINAL_REACHABILITY.json').read_text())['rows'];z=np.load(JOB['table']);g=Geometry(x,{k:z[k]for k in ['bounds','centers']});e=Engine(x['setup']);probes=[];selected=None;error=None;backups=[];modelerr=None
 try:
  for wait in range(0,2000,50):
   schedule=([(0.,0.,wait,0)]if wait else[])+rows;ss,uu=e.simulate(initial(x['packet']),schedule);p,_=g.final(x,ss,uu,schedule);probes.append({'initial_wait_native':wait,'passed':p['passed'],'minimum_static_m':p['minimum_static_m'],'minimum_timed_dynamic_m':p['minimum_timed_dynamic_m'],'failed_checks':[k for k,v in p['checks'].items()if not v]});dump(O/'PROBES.json',probes)
   if p['passed']:selected={'rows':schedule,'proof':p,'wait_native':wait};break
  if selected:
   ps,pu,mem,episodes,active=python_replay(x['setup'],initial(x['packet']),selected['rows']);COUNTS['python_native']+=len(pu);modelerr=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));assert modelerr<=1e-8,'INDEPENDENT_MODEL_MISMATCH';dump(O/'SELECTED.json',selected);np.savez_compressed(O/'SELECTED_SOURCE.npz',states=ps,controls=pu)
   for i in range(0,len(pu)-2200,125):
    origin={'state':ps[i].copy(),'last_ctrl':mem[i,:4].copy(),'integral':float(mem[i,4]),'coupled_episode':bool(episodes[i]),'steering_motion_active':bool(active[i])};bs,bu=e.simulate(origin,[(0.,0.,2200,0)]);packet=forecast_packet(x['packet'],ps[i],mem[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bp,_=g.final(dict(x,packet=packet,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist()),bs,bu,[(0.,0.,2200,0)]);backups.append({'native':i,'passed':bp['passed'],'failed_checks':[k for k,v in bp['checks'].items()if not v]});dump(O/'BACKUPS.json',backups)
 except BaseException as err:
  import traceback
  error={'error':repr(err),'traceback':traceback.format_exc()};dump(O/'ERROR.json',error)
 finally:signal.alarm(0)
 answer={'closed':True,'passed':bool(selected and backups and all(b['passed']for b in backups)and error is None),'full_source_passed':selected is not None,'probes':len(probes),'best_minimum_timed_dynamic_m':max((p['minimum_timed_dynamic_m']for p in probes),default=None),'backup_count':len(backups),'counts':{'analytical_cpp_native':e.native,'independent_python_native':COUNTS['python_native']},'maximum_model_error':modelerr,'error':error,'wall_s':time.monotonic()-start,'models':0,'physical_integrations':0,'no_physical_launch':True};dump(O/'COMPLETION.json',answer);print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
