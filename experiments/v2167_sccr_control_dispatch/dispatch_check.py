"""Exact v2/v3 control entries in explicit nonphysical source shells, no neural calls."""
from source_graph import R,ROOT,sha
from pathlib import Path
import ast,copy,json,os,math,hashlib
from typing import Any
import numpy as np
S=R/'runs'/Path(__file__).resolve().parent.name
V2=ROOT/'training/phase21_risk_switch_fusion_sac/envs/mkmini_phase21_v2_corridor_detect_control_failed.py'
V3=ROOT/'training/phase21_risk_switch_fusion_sac/envs/mkmini_phase21_v3_exact_pair_baseline.py'
assert os.sched_getaffinity(0)=={0}and not(S/'RESULT.json').exists()
old=R/'runs/v2166_sccr_import_binding_recovery/components/POLICY/RESULT.json';saved=json.loads(old.read_bytes());assert saved['passed'];base=np.array(saved['parity']['107']['direct_actions'][0],np.float32);residual=np.array(saved['parity']['186']['direct_actions'][0],np.float32)
class BaseStub:
 def __init__(self,**kwargs):
  self.phase14_assist_scale=.15;self.robot_radius=.28;self.shield_front_stop=.28;self.shield_front_slow=.45;self.shield_slow_speed=.18;self.shield_turn_gain=.35;self.base_calls=0;self.base_step_calls=0;self.risk_calls=0;self.detour_calls=0;self.apply_calls=0;self.api_len=5;self.received=None
 def _base_action(self,raw):self.base_calls+=1;assert np.asarray(raw).shape==(127,);return base.copy()
 def step(self,action):
  self.base_step_calls+=1;self.received=np.asarray(action,np.float32).copy();answer=(np.zeros(186,np.float32),0.,False,False,{})
  return answer if self.api_len==5 else(answer[0],answer[1],False,answer[-1])
 def _phase21_compute_corridor_state(self):self.risk_calls+=1
 def _phase21_v3_build_detour(self):self.detour_calls+=1;return False
 def _phase21_v3_apply_path(self,path):self.apply_calls+=1;return 1
 def _phase21_fill_info(self,info,**kwargs):return dict(info,explicit_stub_telemetry=True,**kwargs)
 def _phase21_v3_fill_info(self,info):return dict(info,explicit_stub_telemetry=True)
space=dict(np=np,math=math,Any=Any,Phase20UnknownAdaptationEnv=BaseStub)
def install(path,name,parent,methods):
 tree=ast.parse(path.read_text());original=next(x for x in tree.body if isinstance(x,ast.ClassDef));nodes=[copy.deepcopy(n)for n in original.body if isinstance(n,ast.FunctionDef)and n.name in methods]
 assert {n.name for n in nodes}==set(methods)
 constants=[copy.deepcopy(n)for n in original.body if isinstance(n,ast.Assign)and all(isinstance(t,ast.Name)and t.id.startswith('MODE_')for t in n.targets)]
 cls=ast.ClassDef(name=name,bases=[ast.Name(id=parent,ctx=ast.Load())],keywords=[],body=constants+nodes,decorator_list=[])
 exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),str(path),'exec'),space)
 return space[name],{n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()for n in nodes}
V2Shell,a2=install(V2,'Phase21V2CorridorEnv','Phase20UnknownAdaptationEnv',['__init__','_base_action','step','_phase21_update_mode','_phase21_apply_action_scale','_phase21_steer_gain','_phase21_min_speed_scale'])
V3Shell,a3=install(V3,'ExactPairV3SourceShell','Phase21V2CorridorEnv',['__init__','_base_action','step'])
rows=[]
for mode,risk in [('TRACK',0.),('ASSIST',.3),('AVOID',.9)]:
 for api in [4,5]:
  objects=[]
  for label,cls in [('v2',V2Shell),('v3',V3Shell)]:
   obj=cls();obj.phase21_mode=mode;obj.phase21_last_risk=risk;obj.phase21_last_steer_direction=1.;obj.phase21_last_front_min=1.;obj.api_len=api
   original=obj._base_action(np.zeros(127,np.float32));reply=obj.step(residual.copy());assert len(reply)==api and obj.base_calls==obj.base_step_calls==1 and obj.risk_calls==2
   objects.append((label,obj,original))
  _,v2,b2=objects[0];_,v3,b3=objects[1]
  assert np.array_equal(b3,base)and np.array_equal(v3.received,residual)and v3.phase14_assist_scale==.15
  expected=residual.copy()
  if mode!='TRACK':expected[0]+=.35*risk;expected[1]-=.45*risk
  expected=np.clip(expected,-1.,1.);assert np.array_equal(v2.received,expected)
  if mode=='TRACK':assert np.array_equal(b2,b3)and np.array_equal(v2.received,v3.received)
  else:assert not np.array_equal(b2,b3)and not np.array_equal(v2.received,v3.received)
  assert v3.detour_calls==(0 if mode=='TRACK' else 1)
  rows.append(dict(mode=mode,risk=risk,api=api,v2_base_action=b2.tolist(),v3_base_action=b3.tolist(),v2_forwarded_residual=v2.received.tolist(),v3_forwarded_residual=v3.received.tolist(),v3_bypasses_v2_action_layers=True,v3_detour_stub_calls=v3.detour_calls,actual_physics=0))
# Explicit active-path dispatch branch; function remains original, path sink is a stub.
a=V3Shell();a.phase21_v3_detour_applied=True;a.phase21_v3_active_path=np.array([[0.,0.],[1.,0.],[2.,0.]],np.float32);a.step(residual.copy());assert a.apply_calls==1 and np.array_equal(a.received,residual)
graph=json.loads((S/'SOURCE_GRAPH.json').read_bytes());assert graph['passed'];provider=graph['outer_conditional_branches'][0]['providers'];assert'mkmini_phase21_v3_exact_pair_baseline.py'in provider['_base_action']['provider']and'mkmini_phase21_v2_corridor_detect_control_failed.py'in provider['_phase17_apply_safety_shield']['provider']
v=dict(passed=True,closed=True,scope='PURE_ORIGINAL_CONTROL_DISPATCH_SOFTWARE_COMPONENT',cases=rows,active_path_apply_dispatch_passed=True,original_function_AST_SHA256=dict(v2=a2,v3=a3),source_SHA256={str(p.relative_to(R)):sha(p)for p in [V2,V3,old,Path(__file__),Path(__file__).with_name('source_graph.py')]},models=0,neural_inference=0,physics=0,replay=0,physical_audit=0,original_environment_constructors=0,software_class_shells_with_explicit_base_stub=True,saved_actor_output_used_only_as_nonphysical_fixture=True,actual_SCCR_entry_uses_v3_path_recovery_not_v2_action_injection=True,original_v2_shield_and_sensor_risk_still_inherited=True,whole_control_chain_or_live_SCCR_qualified=False,formal_tasks=0)
raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<128*1024;(S/'RESULT.json').write_bytes(raw);print(json.dumps({k:x for k,x in v.items()if k not in ['cases','source_SHA256','original_function_AST_SHA256']}))
