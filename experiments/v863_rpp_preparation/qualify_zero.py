"""Config and actual unchanged actuator Adapter interface, no MuJoCo model."""
import ast,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v863_rpp_preparation'
sys.path.insert(0,str(R/'experiments/v862_ready_static'));from handshake import verify_sources
verify_sources(R,R/'experiments/v862_ready_static/SOURCE_FREEZE.json')
old=json.loads((R/'experiments/v862_ready_static/nav2_params.yaml').read_text());current=json.loads((C/'nav2_params.yaml').read_text());only=json.loads(json.dumps(current));only['controller_server']['ros__parameters']['FollowPath']=old['controller_server']['ros__parameters']['FollowPath'];assert only==old
params=current['controller_server']['ros__parameters']['FollowPath'];assert params['use_rotate_to_heading']is False and params['allow_reversing']is True and params['use_collision_detection']is True;assert params['inflation_cost_scaling_factor']==current['local_costmap']['local_costmap']['ros__parameters']['inflation_layer']['cost_scaling_factor']==4.
sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'));sys.path.insert(0,str(R/'experiments/v855_renewal_worker'));from vehicle_control import Adapter
class Names:
 mjtObj=SimpleNamespace(mjOBJ_ACTUATOR=0)
 @staticmethod
 def mj_name2id(m,kind,name):return ['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act'].index(name)
m=SimpleNamespace(actuator_ctrllimited=np.ones(4),actuator_ctrlrange=np.array([[-.52,.52],[-.52,.52],[-20.,20.],[-20.,20.]]));a=Adapter(m,Names);calls=0
for desired in [(0.,0.),(.2,0.),(.2,.2),(.2,-.2),(-.15,.2),(-.15,-.2),(0.,0.)]:
 for _ in range(40):
  before=a.last.copy();u=a.compute(*desired,0.,0.,desired==(0.,0.));assert np.isfinite(u).all()and a.commands.legal(u);assert np.max(abs(u-before)-a.commands.rate*.01/.08)<=1e-10;calls+=1
for p in C.glob('*.py'):ast.parse(p.read_text())
actual=json.loads((O/'software02/RESULT.json').read_text());assert actual['passed'];assert not(R/'runs/v858_nav2_verified/v863_rpp_static').exists();assert json.loads((C/'AUTHORIZATION_TEMPLATE.json').read_text())['models_authorized']is False
result=dict(passed=True,only_FollowPath_changed=True,old_model_map_sensor_actuator_source_unchanged=True,plugin_software_all_seven_active=True,correct_inflation_coefficient=4.,fake_adapter_calls=calls,original_adapter_sha256=hashlib.sha256((R/'experiments/v856_nav2_foundation/vehicle_control.py').read_bytes()).hexdigest(),vehicle_models=0,native_integrations=0,actual_physical_controller_response_not_tested=True,synthetic_actuator_limits_only=True,physical_candidate_authorized=False);(O/'ZERO_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
