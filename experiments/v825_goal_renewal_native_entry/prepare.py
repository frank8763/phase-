"""No-model replay of the actual old select interface, before source freeze."""
import importlib.abc,json,sys
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('PREPARATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
from helpers import *
from exact_footprint import build
from motion_tracker import install_time_gate
from serial_predictor import RobotPredictor
from actuator_commands import CommandMap
from learned_proposer import Proposer
from self_geometry import containment_margin
import importlib.util
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
protocol=read(pair/'STATIC_PROTOCOL.json');traces,states,decisions,routes=fixed_inputs();rows=[]
for step in (282,500):
 data=SimpleNamespace(qpos=np.asarray(traces[step-1]['qpos_full']),qvel=np.asarray(traces[step-1]['qvel_full']))
 env=environment(SimpleNamespace(opt=SimpleNamespace(timestep=.01)),data);current=pose(data.qpos)
 predictor=object.__new__(RobotPredictor);predictor.prediction_steps=0;predictor.enable_differential=True
 predictor.proposer=Proposer(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json')
 contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');mapping=object.__new__(CommandMap);mapping.ids=contract['ids'];mapping.lower=np.asarray(contract['limits'])[:,0];mapping.upper=np.asarray(contract['limits'])[:,1];mapping.rate=np.asarray(contract['rate']);predictor.command_map=mapping
 old=decisions[step];cursor=[0]
 def predict(real,target,ids,last_command,horizon=240,brake_after=None):
  item=old['candidates'][cursor[0]];cursor[0]+=1;z=np.load(cell/'nominal_forecasts'/item['nominal_saved_forecast'])
  assert np.max(abs(z['target']-target))<=1e-12,'ORIGINAL_TARGET_COMMAND_MISMATCH'
  predictor.terminal_speed=float(np.linalg.norm(z['terminal_qvel'][:2]));predictor.prediction_self_margin=float(containment_margin(z['self_bounds'],np.asarray(protocol['footprint_bounds'])).min());predictor.prediction_self_contained=predictor.prediction_self_margin>=.002
  predictor.prediction_steps+=240
  return z['poses']
 predictor.predict=predict
 world=copy.deepcopy(read(cell/'planning_0265.json')['causal_input']);world['rectangles']=[*protocol['known_rectangles'],states[step]['current_outer_rectangle']]
 field=build(F,world);field.nominal_static_geometry=SimpleNamespace(half=field.half,center_local=field.center_local,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=field.config)
 install_time_gate(field,states[step],'predictive',protocol['known_circles'],protocol['known_rectangles'])
 features=old['candidates'][0]['features'];last=np.asarray(traces[step-1]['ctrl'])[contract['ids']]
 command,gate=predictor.select(env,field,np.asarray(routes[step]['reference_path']),routes[step]['index'],current,features[10],features[11],last)
 old_best=max((a for a in old['candidates']if a['reason']is None),key=lambda a:a['score'])
 assert np.max(abs(command-old_best['first_command']))<=1e-12 and abs(gate['score']-old['summary']['score'])<=1e-10
 assert len(predictor.last_diagnostics)==len(old['candidates'])
 for a,b in zip(predictor.last_diagnostics,old['candidates']):
  assert a['reason']==b['reason']and np.max(abs(np.asarray(a['target_command'])-b['target_command']))<=1e-12
  if a['reason']is None:assert abs(a['score']-b['score'])<=1e-10
 reference,source=new_reference(step);assert np.max(abs(reference[0,:3]-current))<=1e-12
 rows.append(dict(step=step,old_saved_candidate_count=cursor[0],old_select_command_score_and_reasons_exact=True,new_reference_source=str(source.relative_to(repo)),new_reference_goal_distance=float(np.linalg.norm(reference[-1,:2]-protocol['goal_xy'])),new_reference_controls=controls_for_reference(reference,current,env,np.asarray(protocol['goal_xy']))))
out=dict(status='FIXED_OLD_CONTROLLER_INTERFACE_ZERO_MODEL_PASS',records=rows,models=0,integrations=0,scope='Stored original forecasts only; not new native control qualification')
dump(repo/'runs/goal_renewal_20261105/V825_PREPARATION.json',out);print(json.dumps(out))
