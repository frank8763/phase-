"""Saved array comparisons only, zero physical/model/solver/audit calls."""
from pathlib import Path
import hashlib,importlib.abc,json,os,sys,time
class Ban(importlib.abc.MetaPathFinder):
 def find_spec(self,n,*a):
  if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('SAVED_ARRAY_MATH_ONLY:'+n)
sys.meta_path.insert(0,Ban());os.sched_setaffinity(0,{4})
import numpy as np
R=Path(__file__).resolve().parents[2];S=R/'runs'/Path(__file__).resolve().parent.name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=R/'runs/v2095_svg_common_full_route/rounds';A=P/'common_02__SVGMPPI';B=P/'common_03__SVGMPPI'
assert not(S/'SVG03_PREFIX_PHASE_READOUT.json').exists();start=time.monotonic()
a=read(A/'actual/RESULT.json');b=read(B/'actual/RESULT.json');assert a['closed']and b['closed']
rows={}
with np.load(A/'actual/FULL_STATE_NPLUS1.npz')as x,np.load(B/'actual/FULL_STATE_NPLUS1.npz')as y:
 for k in x.files:
  assert x[k].shape==y[k].shape
  rows[k]=dict(shape=list(x[k].shape),bitwise_equal=x[k].tobytes()==y[k].tobytes(),maximum_absolute_difference=float(abs(x[k]-y[k]).max())if x[k].size else 0.)
aj=read(A/'actual/APPLIED_JOURNAL.json');bj=read(B/'actual/APPLIED_JOURNAL.json')
requests_equal=[r['request']for r in aj]==[r['request']for r in bj]
ta=read(A/'PILOT_TASK.json');tb=read(B/'PILOT_TASK.json')
value=dict(closed=True,models=0,solver_calls=0,physics=0,replay=0,new_independent_audit=False,new_trials=0,task_ids=[ta['task_id'],tb['task_id']],phases=[ta['phase'],tb['phase']],same_sensor_seed=ta['seed']==tb['seed'],arrays=rows,actual_requested_commands_equal=requests_equal,actual_counts=[a['new_actual_native'],b['new_actual_native']],first_actor_detection=[a['physical']['first_actor_detection'],b['physical']['first_actor_detection']],both_whole_goal_false=not a['passed']and not b['passed'],both_primary=[a['first_error']['error'],b['first_error']['error']],interpretation='Vehicle trace coincidence over these closed prefixes only; actor phase/mocap differs; no observed actor here. No global phase invariance, mechanism gain or independent success is established.',input_SHA256={str(p.relative_to(R)):sha(p)for p in [A/'actual/FULL_STATE_NPLUS1.npz',B/'actual/FULL_STATE_NPLUS1.npz',A/'actual/APPLIED_JOURNAL.json',B/'actual/APPLIED_JOURNAL.json',A/'actual/RESULT.json',B/'actual/RESULT.json']},late_local_analysis_not_in_previously_sealed_runtime=True,wall_s=time.monotonic()-start)
raw=json.dumps(value,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<1024**2 and time.monotonic()-start<60;(S/'SVG03_PREFIX_PHASE_READOUT.json').write_bytes(raw)
print(json.dumps(dict(requests_equal=requests_equal,arrays=rows,first_actor_detection=value['first_actor_detection'])))
