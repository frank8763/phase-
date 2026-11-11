"""Bitwise old-domain preservation, bounded new term, and real saved red/green."""
import copy,importlib.abc,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1044_curvature_speed_prediction'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));from whole_input import Predictor,PARAMETERS,initial,old
fixture=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text());setup=fixture['setup'];packet=fixture['packet'];steps=0
for k in [-.758770385,-.3793851925,0.,.3793851925,.758770385]:
 a=old.Predictor(setup,initial(packet),old.PARAMETERS);b=Predictor(setup,initial(packet),PARAMETERS)
 for req in [[.03,.03*k,False]]*300+[[0.,0.,False]]*200:
  x,u=a.step(*req);y,v=b.step(*req);assert np.array_equal(x,y)and np.array_equal(u,v);steps+=1
negative=[]
for name,change in [('positive_coefficient',dict(curvature_speed_coefficient=.01)),('nan_coefficient',dict(curvature_speed_coefficient=math.nan)),('wrong_domain',dict(curvature_speed_domain_m_s=.09))]:
 try:Predictor(setup,initial(packet),dict(PARAMETERS,**change))
 except AssertionError:negative.append(name)
 else:raise AssertionError('INVALID_PARAMETER_ACCEPTED '+name)
# Unsaturated scalar speed/PI subsystem Jury criteria hold over the entire
# curvature-square interval; entries are affine in the positive speed gain.
b0=PARAMETERS['speed_discrete'][1];b1=b0+PARAMETERS['curvature_speed_coefficient']*(math.tan(.42722137342572125)/.6)**2;a=PARAMETERS['speed_discrete'][0]
checks=[]
for b in [b0,b1]:
 matrix=np.array([[a-8.04*b,4*b],[-.01,1.] ]);tr=float(np.trace(matrix));det=float(np.linalg.det(matrix));checks.append(1-tr+det>0 and 1+tr+det>0 and 1-det>0)
assert min(b0,b1)>0 and all(checks)
red=json.loads((R/'runs/v1043_speed_predictor_identification/DIAGNOSIS.json').read_text())['old']['left'];green=json.loads((O/'SAVED_QUALIFICATION.json').read_text());assert not red['all_original_response_position_heading_gates']and green['passed']
# Production audit rejects out-of-batch writes before any read or file output.
s=importlib.util.spec_from_file_location('v1044_model_qualified_audit',C/'audit.py');audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit)
try:audit.audit(dict(output=str(R/'runs/v858_nav2_verified/v1024/dynamic_we')),save=True)
except AssertionError:negative.append('audit_write_outside_batch')
else:raise AssertionError('OLD_AUDIT_WRITE_ACCEPTED')
out=dict(passed=True,models=0,integrations=0,old_domain_bitwise_steps=steps,coefficient=PARAMETERS['curvature_speed_coefficient'],all_curvature_positive_speed_gain_interval=[b1,b0],unsaturated_speed_pi_jury_entire_interval=True,rejected_negative_cases=negative,old_saved_left_red_m=red['maximum_position_m'],new_saved_left_green_m=green['results']['left']['maximum_position_m'],physical_qualification=False)
(O/'MODEL_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
