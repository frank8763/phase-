"""Config-only qualification after expiry. No ROS, model or navigation launch."""
import ast,copy,hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v865_global_margin_preparation'
def main():
 old=json.loads((R/'experiments/v863_rpp_preparation/nav2_params.yaml').read_text());new=json.loads((C/'nav2_params.yaml').read_text());expected=copy.deepcopy(old);expected['global_costmap']['global_costmap']['ros__parameters']['footprint_padding']=.20
 assert new==expected and old['global_costmap']['global_costmap']['ros__parameters']['footprint_padding']==.15
 assert new['local_costmap']==old['local_costmap']and new['controller_server']==old['controller_server']and new['collision_monitor']==old['collision_monitor']
 assert json.loads((C/'AUTHORIZATION_TEMPLATE.json').read_text())['models_authorized']is False
 for n,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h
 for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 baseline=json.loads((O/'original02/PLAYBACK_COMPLETION.json').read_text());assert baseline['model_integrations']==0 and baseline['recorded_ticks_served']==0
 result=dict(config_only_passed=True,only_change='global footprint_padding .15 to .20m',local_controller_and_safety_unchanged=True,source_readback_passed=True,original_configuration_stationary_plan_capture=True,new_margin_configuration_ros_test_executed=False,new_margin_physical_navigation_executed=False,qualified_for_physical=False,status='PREPARED_NOT_QUALIFIED_FOR_PHYSICS',root_model_deadline_expired=True,old_deadline_unix=1794062038.6753576,no_new_window_created=True,model_initializations=0,model_integrations=0,new_ros_servers=0,at=time.time())
 (O/'PREPARATION_STATUS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
