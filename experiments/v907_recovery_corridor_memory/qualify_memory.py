"""Actual saved second-request red/green and counterfactual audit tamper checks; zero models."""
import copy,importlib.abc,json,shutil,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v907_recovery_corridor_memory'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,*args):
        if fullname.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle','factory'}:raise AssertionError('FORBIDDEN_MODEL_IMPORT')
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from refuge_logic import choose_refuge,retained_suffix,exit_path_ok
sys.path.insert(0,str(C));from refuge_audit import audit_refuge
source=R/'runs/v858_nav2_verified/v905/main_we';saved=json.loads((source/'REFUGE_SUPERVISION.json').read_text());a,b=[x for x in saved['events']if x['event']=='REFUGE_REQUEST'];known=json.loads((source/'physics/SETUP.json').read_text())['known'];s=b['source'];memory=[dict(native_tick=a['native_tick'],selection=a['selection'])]
old=choose_refuge(b['body'],b['breadcrumbs'],s['support_bounds'],s['source_age_s'],known)
new=choose_refuge(b['body'],b['breadcrumbs'],s['support_bounds'],s['source_age_s'],known,memory)
checks=dict(original_actual_second_request_rejected=old is None and b['selection'] is None,new_currently_revalidated_route_admitted=new is not None)
assert new is not None
expected,tracking=retained_suffix(b['body'],a['selection']['reference_path'])
checks['exact_previous_measured_corridor']=np.array_equal(new['reference_path'],expected) and new['source_refuge_request_native_tick']==a['native_tick']
checks['same_unrelaxed_exit_contract']=new['geometry_contract']==exit_path_ok(expected,s['support_bounds'],s['source_age_s'],known)
checks['current_tracking_deviation_within_original_limit']=tracking['measured_reference_distance_m']<=.04
bad=list(b['body']);bad[1]-=1.
checks['reject_current_off_corridor']=choose_refuge(bad,[],s['support_bounds'],s['source_age_s'],known,memory)is None
checks['reject_stale_source']=choose_refuge(b['body'],[],s['support_bounds'],100.,known,memory)is None
checks['reject_current_blockage']=choose_refuge(b['body'],[],np.zeros(16)+100.,0.,known,memory)is None
fixture=O/'counterfactual_audit_fixture';(fixture/'physics').mkdir(parents=True)
for name in ['physics/NATIVE_TRACE.npz','physics/SETUP.json','MOTION_ENVELOPE.json.gz','ROUTER_REQUESTS.json']:shutil.copyfile(source/name,fixture/name)
changed=copy.deepcopy(saved);changed['events'][-1]['selection']=new
(fixture/'REFUGE_SUPERVISION.json').write_text(json.dumps(changed)+'\n')
proof=audit_refuge(fixture);checks['counterfactual_selection_causal_audit']=proof['passed'] and proof['causal_refuge_requests']==2
changed['events'][-1]['selection']['source_refuge_request_native_tick']+=1
(fixture/'REFUGE_SUPERVISION.json').write_text(json.dumps(changed)+'\n')
try:audit_refuge(fixture)
except AssertionError:checks['reject_memory_source_tamper']=True
else:checks['reject_memory_source_tamper']=False
receipt=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,source_failed_tick=b['native_tick'],new_selection=new,scope='Saved real V905 failure is red without memory; green selection is counterfactual only, not executed navigation. Audit fixture explicitly synthetic and final tampered input retained. Old V905 is unchanged.')
(O/'MEMORY_QUALIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(passed=receipt['passed'],checks=checks,geometry=new['geometry_contract'])));assert receipt['passed']
