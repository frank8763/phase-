from pathlib import Path
import os,json,math,hashlib,importlib.util
from domain import project
R=Path(__file__).resolve().parents[2];O=R/'runs/v2174_shared_virtual_command_domain'
assert os.sched_getaffinity(0)=={0}and not(O/'RESULT.json').exists()
p=R/'experiments/v1288_baseline_interface/contract.py';spec=importlib.util.spec_from_file_location('original_common_contract',p);contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
rows=[]
for label,s,w in [('zero',0.,0.),('straight',0.,.5),('left',.2,.5),('right',-.2,.5),('reverse_left',.2,-.5),('deadband',.2,.01),('speed_saturation',.2,35.04),('curvature_saturation',1.0,2.)]:
 x=project(dict(virtual_steer_rad=s,virtual_wheel_rad_s=w,wheel_radius_m=.12,wheelbase_m=.6));v,omega,_=x['request'];contract.twist(v,omega)
 if not x['speed_saturated']and not x['curvature_saturated']and not x['deadband_applied']:
  assert abs(v-w*.12)<1e-15 and abs(omega-v*math.tan(s)/.6)<1e-15
 if abs(v)>0:assert v*w>0
 if abs(omega)>0:assert omega*v*s>0
 if label=='curvature_saturation':assert abs(abs(omega/v)-1/1.32)<1e-15
 rows.append(dict(case=label,output=x))
assert rows[2]['output']['request'][0]==rows[3]['output']['request'][0]and rows[2]['output']['request'][1]==-rows[3]['output']['request'][1]
base=dict(virtual_steer_rad=.2,virtual_wheel_rad_s=2.,wheel_radius_m=.12,wheelbase_m=.6)
neg=[]
for label in ['nan','bool','zero_radius','negative_base','degrees_instead_of_rad','extra','missing','nondict']:
 q=base.copy()
 if label=='nan':q['virtual_wheel_rad_s']=float('nan')
 if label=='bool':q['virtual_steer_rad']=True
 if label=='zero_radius':q['wheel_radius_m']=0.
 if label=='negative_base':q['wheelbase_m']=-.6
 if label=='degrees_instead_of_rad':q['virtual_steer_rad']=35.
 if label=='extra':q['hidden_actor_truth']=[0.,0.]
 if label=='missing':del q['wheelbase_m']
 if label=='nondict':q=[]
 try:project(q)
 except ValueError as e:neg.append(dict(case=label,reason=str(e)))
 else:raise AssertionError('BAD_INPUT_ACCEPTED:'+label)
f=R/'runs/v2173_sccr_inner_control_readout/RESULT.json';original=json.loads(f.read_text());fixtures=[]
for row in original['saved_frames']:
 a=row['result'];params=a['source_default_effective_parameters'];x=project(dict(virtual_steer_rad=a['virtual_steer_rad'],virtual_wheel_rad_s=a['virtual_wheel_rad_s'],wheel_radius_m=params['wheel_radius'],wheelbase_m=params['wheel_base']));contract.twist(*x['request'][:2]);fixtures.append(dict(native=row['native'],output=x))
r=dict(passed=True,scope='PURE_EXPLICIT_COMMON_COMMAND_DOMAIN_ONLY',fixed_cases=rows,negative_cases=neg,saved_inner_output_fixtures=fixtures,
      inherited_raw_output_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),unchanged_common_contract_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
      controller_NN_render_model_physics_replay_audit_source_or_formal_calls=0,full_SCCR_or_common_plant_controller_qualified=False,
      software_helper_sha256=hashlib.sha256((Path(__file__).parent/'domain.py').read_bytes()).hexdigest(),
      shared_uniform_adapter_disclosure_required_before_confirmation=True)
raw=json.dumps(r,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<65536;(O/'RESULT.json').write_text(raw)
print(json.dumps({'passed':True,'fixed_cases':len(rows),'negative_cases':len(neg),'saved_output_fixtures':len(fixtures),'new_NN_or_physics':0}))
