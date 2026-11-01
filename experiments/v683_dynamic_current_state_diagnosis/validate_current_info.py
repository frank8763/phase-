"""804 old instants: current-only payload and unchanged future coverage; no integration."""
import os,sys,time,json,hashlib,signal,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from current_state_oracle import evaluator_current_packet,state_from_packet
from motion_evaluator import check_forecast
from motion_tracker import SPEED,ACCEL
from union_belief import future_cells
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent;root=repo/'runs/v683_dynamic_current_state_diagnosis';p=root/'PRE_NAV_VALIDATION.json';assert not p.exists();read=lambda p:json.loads(p.read_text());base=repo/'runs/v680_dynamic_later_stop_reserve/dev47_95000011_laterstop/paired';config=read(base/'DYNAMIC_PROTOCOL.json');rows=[json.loads(s)for s in(base/'geometry_memory/motion_estimate.jsonl').read_text().splitlines()];started=time.monotonic();status='FAILED';error=None;count=0;worst=0.;maxcoverage=-1e9;signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('180S_INFO_VALIDATION')));signal.alarm(180)
class SavedActor:
 def __init__(self,c):self.config=c
 def xy(self,t):return np.asarray(self.config['anchor_xy'])+np.asarray(self.config['axis_xy'])*self.config['amplitude_m']*np.sin(t*self.config['omega_rad_s']+self.config['phase_rad'])
try:
 assert SPEED==.12 and ACCEL==.04 and len(rows)==804
 for row in rows:
  now=row['time'];packet=json.loads(json.dumps(evaluator_current_packet(SavedActor(config),now)));assert set(packet)=={'time','position','velocity'}
  state=state_from_packet(packet);expected=np.asarray(config['anchor_xy'])+np.sin(now*.32)*.25*np.asarray(config['axis_xy']);expectedv=np.cos(now*.32)*.08*np.asarray(config['axis_xy']);errornow=float(max(np.max(abs(np.asarray(state['center'])-expected)),np.max(abs(np.asarray(state['velocity'])-expectedv))));worst=max(worst,errornow);assert errornow<=1e-12
  assert state['information_role']=='ORACLE_CURRENT_STATE_ONLY'and state['hidden_world_geometry_used']is True
  assert state['position_lower']==state['position_upper']and state['velocity_lower']==state['velocity_upper']and len(state['outer_state_cells'])==1
  assert not any(k in state or k in packet for k in ['anchor_xy','axis_xy','amplitude_m','phase_rad','omega_rad_s','future','swept_envelope_reference'])
  coverage=check_forecast(config,state);maxcoverage=max(maxcoverage,coverage['maximum_future_center_union_excess_m']);assert coverage['passed']and coverage['checked_future_samples']==329;count+=1
 unchanged={name:hashlib.sha256((src/name).read_bytes()).hexdigest()==hashlib.sha256((repo/'experiments/v680_dynamic_later_stop_reserve'/name).read_bytes()).hexdigest()for name in ['planner.py','task_planner.py','serial_predictor.py','geometry_predictor.py','robot_predictor.py','motion_tracker.py','union_belief.py','reserved_recovery.py','actuator_commands.py','joint_admission.py','dynamic_scene.py','replay_native_audit.py']};assert all(unchanged.values())
 old=(repo/'experiments/v680_dynamic_later_stop_reserve/recovery_supervisor.py').read_text();assert (src/'recovery_supervisor.py').read_text().split('class RecoverySupervisor:',1)[1]==old.split('class RecoverySupervisor:',1)[1]
 status='PASS'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 signal.alarm(0);result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'registered_instants':len(rows),'checked_instants':count,'maximum_exact_current_state_error':worst,'maximum_future_center_union_excess_m':maxcoverage,'future_times_per_instant':329,'unchanged_control_dependencies':locals().get('unchanged',{}),'robot_integrations':0,'navigation_tasks':0,'information_role':'ORACLE_CURRENT_STATE_ONLY','counts_as_unknown_dynamic_success':False,'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in src.glob('*.py')},'input_sha256':{str(f.relative_to(repo)):hashlib.sha256(f.read_bytes()).hexdigest()for f in[base/'DYNAMIC_PROTOCOL.json',base/'geometry_memory/motion_estimate.jsonl']}};p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['source_sha256','input_sha256']},indent=2));assert status=='PASS',error
