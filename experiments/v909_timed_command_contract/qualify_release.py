"""Pre-freeze real loader identities and independent saved-record negative cases."""
import ast,copy,gzip,importlib.abc,importlib.util,json,shutil,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v909_timed_command_contract'
class BlockModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','factory'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN')
sys.meta_path.insert(0,BlockModel());sys.path.insert(0,str(C))
import native_worker
checks=dict(native_loader_selects_new_contract=native_worker.engine.Startup.__module__=='native_contract',native_loader_new_authority=native_worker.engine.authorized.__module__=='authority')
sys.path.insert(0,str(C));import ros_worker
checks['ros_loader_selects_new_source']=ros_worker.engine.C==C
sys.path.insert(0,str(C));import motion_publisher
sys.path.insert(0,str(C));import dynamic_proxy
sys.path.insert(0,str(C));import supervise
checks['same_production_publisher_identity']=Path(motion_publisher.__file__).parent==C
checks['same_production_proxy_identity']=Path(dynamic_proxy.__file__).parent==C
checks['same_production_supervisor_identity']=Path(supervise.__file__).parent==C
checks['all_candidate_python_parses']=all(ast.parse(p.read_text())is not None for p in C.glob('*.py'))
from command_tube import admit
sys.path.insert(0,str(C));from tube_audit import audit_tubes
saved=O/'saved';fixture=O/'audit_fixture';(fixture/'physics').mkdir(parents=True,exist_ok=True)
for name in ['NATIVE_TRACE.npz','SETUP.json']:shutil.copyfile(saved/name,fixture/'physics'/name)
shutil.copyfile(saved/'MOTION_ENVELOPE.json.gz',fixture/'MOTION_ENVELOPE.json.gz')
known=json.loads((saved/'SETUP.json').read_text())['known']
with np.load(saved/'NATIVE_TRACE.npz')as z:
    q=z['qpos'];vel=z['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    bodies=np.c_[q[:,:2],yaw,vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw),vel[:,5]]
events=json.loads((saved/'REFUGE_SUPERVISION.json').read_text())['events'];rows=[]
for e in events:
    if e['event']!='REFUGE_REQUEST':continue
    p=dict(native_tick=e['native_tick'],body=bodies[e['native_tick']-1].tolist(),sent_at=100.,body_measured_at=100.)
    s=e['source'];proof=admit(p,s,0.,0.,known,100.)
    rows.append(dict(packet=p,source=s,wanted=[0.,0.],proof=proof))
# These two completion labels are synthetic harness inputs, never claimed physical results.
(fixture/'ROS_RESULT.json').write_text('{"harness_synthetic_status":true}')
(fixture/'RESULT.json').write_text('{"status":"NATIVE_COMPLETE","harness_synthetic_status":true}')
def check(data):
    with gzip.open(fixture/'COMMAND_TUBES.json.gz','wt')as f:json.dump(data,f)
    return audit_tubes(fixture)
checks['independent_audit_matches_real_body_and_source']=check(rows)['passed']
bad=copy.deepcopy(rows);bad[0]['packet']['body'][0]+=.001
checks['body_tamper_rejected']=not check(bad)['passed']
bad=copy.deepcopy(rows);bad[0]['source']['support_bounds'][0]+=.001
checks['support_tamper_rejected']=not check(bad)['passed']
bad=copy.deepcopy(rows);bad[0]['proof']['v']=.2
checks['command_tamper_rejected']=not check(bad)['passed']
bad=copy.deepcopy(rows);bad[0]['proof']['static_lower_m']=.149
checks['margin_tamper_rejected']=not check(bad)['passed']
checks['fixed18_response_conditions']=len(json.loads((C/'PLATFORM_TASKS.json').read_text()))==18
checks['only_original_we_main_and_repeat']=len(json.loads((C/'TASKS.json').read_text()))==2
result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,synthetic_status_fixture_not_a_physical_pass=True)
(O/'RELEASE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
