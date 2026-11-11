"""Independent saved adoption regeneration; no simulator or new vehicle load."""
import importlib.abc,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1054_atomic_publish';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import predict,checks,Geometry,REQUIRED,dump
from handoff import contained
def main():
 x=json.loads((O/'INPUT_SOURCE.json').read_text());setup=x['setup'];rows=[];total=0
 for p in sorted((O/'software_full_executor/refresh').glob('*/ADOPTED_PLAN.json')):
  record=json.loads(p.read_text());proposal=json.loads(p.with_name('RESULT.json').read_text());assert contained(record['publication_source']['periodic']['vertices'],proposal['source_planes']);ss,uu,rr,mm=predict(setup,record['planning_packet'],record['actions'],tail=False);assert abs(ss-np.array(record['state_path'])).max()<=1e-8;assert abs(uu-np.array(record['predicted_actuator_controls'])).max()<=1e-8;assert np.array_equal(rr,np.array(record['planned_body_requests']));g=Geometry(setup['known'],record['planning_source']['periodic'],record['published_packet']['sim_time']);low=g.complete(ss);cc,upper=checks(ss,uu,rr,record['planning_packet'],setup,np.array(x['goal']),low,REQUIRED);assert all(cc.values());total+=len(ss);rows.append(dict(epoch=p.parent.name,passed=True,native_intervals=len(ss),minimum_raw_m=low,goal_upper_m=upper))
 assert len(rows)==11;execution=json.loads((O/'EXECUTOR_QUALIFICATION.json').read_text());assert execution['passed']and execution['maximum_publish_to_control_s']<=.05;segments=json.loads((O/'software_full_executor/EXECUTION_SEGMENTS.json').read_text());cursor=23640
 for segment in segments:assert segment['start_native']==cursor;assert segment['executed_native']<len(segment['state_path']);cursor+=segment['executed_native']
 assert cursor-23640==execution['new_native'];result=dict(passed=True,epochs=11,independently_regenerated_native_intervals=total,complete_execution_coverage=True,rows=rows,models=0,integrations=0,actual_goal_count=0,physical_ready=False);dump(O/'INDEPENDENT_SOFTWARE_AUDIT.json',result);print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
