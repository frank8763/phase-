"""Real joint selector seam with persisted nominal inputs, synthetic certificates only."""
import copy,gzip,json,os,sys,importlib.abc
from pathlib import Path
from types import SimpleNamespace
import numpy as np
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('NO_MODELS')
sys.meta_path.insert(0,NoModels());R=Path(__file__).resolve().parents[2];W=R/'experiments/v841_early_joint';Q=R/'runs/early_joint_90_20261106/qualification/early_joint_seam_ready02';Q.mkdir()
for p in [R/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1',W]:sys.path.insert(0,str(p))
from early_joint import activate,representatives,select,GUARD_M
from early_joint_independent import check
E=json.loads((W/'FIXED_INPUTS.json').read_text())[0];source=R/'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory';protocol=json.loads((source.parent/'STATIC_PROTOCOL.json').read_text());goal=np.array(protocol['goal_xy']);old=np.load(R/E['original_certificate']);real=SimpleNamespace(qpos=np.asarray(E['state'].get('xy',[0,0])),qvel=np.zeros(1),ctrl=np.zeros(4),time=23.6)
# Saved prefix initial pose is derived from the previous full actual execution row.
rows=[json.loads(s)for s in(source/'v648_execution.jsonl').open()];real.qpos=np.asarray(rows[294]['qpos_full']);real.qvel=np.asarray(rows[294]['qvel_full']);real.ctrl=np.asarray(rows[294]['ctrl'])
safe=sorted([c for c in E['nominal']['candidates']if c['reason']is None],key=lambda c:c['score'],reverse=True);unique=[];seen=set()
for c in safe:
 key=tuple(c['first_command'])
 if key not in seen:
  seen.add(key);z=np.load(source/'nominal_forecasts'/c['nominal_saved_forecast']);unique.append((c['score'],np.array(key),z['poses'],c['minimum_clearance_m'],c['self_domain_margin_m']))
ranks=representatives(unique,real.qpos[:2],goal);assert 1<=len(ranks)<=4
path=np.array(E['reference']['path']);idx=int(np.argmin(np.linalg.norm(path[:,:2]-real.qpos[:2],axis=1)));idx=min(idx,len(path)-2)
class FakeReserve:
 def __init__(self):
  self.cache={'minimum_causal_predicted_clearance_m':GUARD_M+.01};self.cursor=0;self.expected=None;self.expected_ctrl=None;self.finish_pending=False;self.public_goal_xy=goal;self.reference={'path':path.tolist()};self.n=0
 def admit_nominal(self,d,command,field,state,step):
  n=self.n;self.n+=1;minimum=.20+.02*n;q=d.qpos.copy();q[:2]+=.05*(goal-q[:2])/np.linalg.norm(goal-q[:2]);score=minimum+.5*.05
  self.cache=dict(proactive_joint=True,prefix_initial_qpos=d.qpos.copy(),initial_qpos=d.qpos.copy(),initial_qvel=d.qvel.copy(),prefix_command=command.copy(),qpos=np.asarray([q]),minimum_causal_predicted_clearance_m=minimum,minimum_predicted_self_domain_margin_m=.01,terminal_speed_m_s=0.,score=score)
  cs=[dict(library='ORIGINAL',reason=None,selection_score=score)]+[dict(library='FORWARD_EXTENSION',reason='TIME_CLEARANCE')for _ in range(5)]+[dict(library='REFERENCE_FOLLOW',reason='TIME_CLEARANCE',lookahead_m=l,wheel_speed=w,brake_after_native_ticks=b)for l in[.35,.55]for w in[4.,8.,12.]for b in[160,208,240]]
  self.last_attempt=dict(status='APPENDABLE_BACKUP_FOUND',reference_successor_active=True,reference=self.reference,candidates=cs)
  return dict(status='FAKE_NOT_NATIVE',reserve_total_native_ticks=328)
f=FakeReserve();assert not activate(f,E['state'],295);f.cache['minimum_causal_predicted_clearance_m']=E['previous_reserve_minimum_m'];assert activate(f,E['state'],295)and not activate(f,E['state'],296)
chosen=select(f,None,real,E['nominal']['summary'],None,E['state'],295,path,idx,Q,unique);event=json.loads((Q/'early_joint_decisions.jsonl').read_text());assert chosen is not None and event['selected_rank']==ranks[-1];check(Q,event,E['nominal']['candidates'],protocol,source_cell=source)
negative=0
for kind in ['selected_rank','representative','truth','score','command']:
 bad=copy.deepcopy(event)
 if kind=='selected_rank':bad['selected_rank']=-1
 elif kind=='representative':bad['representative_ranks'].append(99)
 elif kind=='truth':bad['hidden_world_geometry_used']=True
 elif kind=='score':bad['probes'][0]['joint_score']+=.1
 else:bad['probes'][0]['first_command'][0]+=.1
 try:check(Q,bad,E['nominal']['candidates'],protocol,source_cell=source)
 except AssertionError:negative+=1
 else:raise AssertionError('UNDETECTED_MUTATION_'+kind)
result=dict(passed=True,fixed_input=295,representative_ranks=ranks,selected_rank=event['selected_rank'],joint_objective_not_first_admissible=True,guard_and_latch=True,independent_selection_reconstruction=True,negative_cases=negative,certificates='SYNTHETIC_SEAM_ONLY_NOT_PHYSICS',models=0,integrations=0)
(Q.parent/'EARLY_JOINT_SEAM_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
