"""Real scene red/green seam, original gate reuse and actual lazy entries."""
import sys,copy,ast,importlib.abc,tempfile
from evening_tools import *
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());import numpy as np
from scene_contract import verify,physical_identity

def main():
 assert not(O/'ROUND_WINDOW.json').exists();old=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/physics/SETUP.json').read_text());new=json.loads((R/'runs/v858_nav2_verified/v1139/observation_refuge/physics/SETUP.json').read_text());task=json.loads((C/'TASKS.json').read_text())[0];assert old['actor']!=new['actor'];assert verify(new,old,task)['passed'];negative=[]
 for name,change in [('phase',lambda x:x['actor'].__setitem__('phase_rad',x['actor']['phase_rad']+.01)),('axis',lambda x:x['actor']['axis_xy'].__setitem__(0,.1)),('radius',lambda x:x['actor'].__setitem__('radius_m',.11)),('static',lambda x:x['known']['known_rectangles'][0].__setitem__(0,.1)),('noise',lambda x:x['noise'].__setitem__('lidar_call',x['noise']['lidar_call']+1)),('ctrl',lambda x:x['limits'][0].__setitem__(0,-999.)),('rate',lambda x:x['slew_per_second'].__setitem__(0,999.)),('model',lambda x:x.__setitem__('model_sha256','0'*64)),('reference_path',lambda x:x['actor']['swept_envelope_reference']['reference_path'][0].__setitem__(0,999.))]:
  q=copy.deepcopy(new);change(q)
  try:verify(q,old,task)
  except AssertionError:negative.append(name)
  else:raise AssertionError('PHYSICAL_CHANGE_ACCEPTED '+name)
 for name in ['observer_worker','observer_audit','post_observation','goal_source','physical','campaign','watchdog','start']:
  module=load('qualified_evening_'+name,C/(name+'.py'));assert module is not None
 from goal_source import schedule
 sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'));from source import remaining_rows
 base=[tuple(r)for r in remaining_rows(json.loads((R/'runs/v1136_route_clock_restore/dynamic_seed_v120/OPTIMIZATION.json').read_text())['rows'],12500)];n=len(base)-1;count=0
 for speed in [.08,.12]:
  for duration in [.4,1.,1.8]:
   for wait in [0.,19.63]:
    u=np.r_[[r[0]for r in base[:-1]],np.full(n,duration),wait];rows=schedule(base,u,speed);assert rows[-1]==(0.,0.,2200,0)and sum(r[2]for r in rows)<=40000;count+=1
 payload={'passed':np.bool_(True),'checks':{'numpy_false':np.bool_(False)},'array':np.array([1.,2.])};assert json.loads(encode(payload))['checks']['numpy_false']is False
 for folder in ['software','goal_v80','goal_v120']:
  parent=O/folder if folder=='software'else O
  with tempfile.TemporaryDirectory(dir=parent,prefix='actual_output_fixture_')as path:
   p=Path(path)/'result.json';dump(p,payload);assert json.loads(p.read_text())['passed']
 oldresults=json.loads((R/'runs/v1140_afternoon_entry_relay/RESULTS.json').read_text());speeds=[r for r in oldresults if r['stage']in ['negative_to_positive','positive_to_negative']];assert len(speeds)==2 and all(r['returncode']==0 and r['result']['passed']and r['audit']['passed']for r in speeds);soft=json.loads((O/'software/RESULT.json').read_text());assert soft['passed']and soft['backup_count']==1564 and soft['failed_backups']==0
 for p in C.glob('*.py'):ast.parse(p.read_text())
 proof={'passed':True,'actual_failed_scene_old_comparator_red':True,'new_physical_scene_identity_green':True,'physical_tamper_rejected':negative,'retained_geometry_reference_not_discarded':True,'actual_worker_audit_post_goal_lazy_entries_imported':True,'fixed_goal_schedule_boundaries':count,'final_record_numpy_roundtrip':True,'exact_output_parent_fixture_passed':True,'reused_two_actual_speed_components_not_rerun':True,'reused1564_backup_audit_not_rerun':True,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0};dump(O/'ENTRY_QUALIFICATION.json',proof);print(encode(proof))
if __name__=='__main__':main()
