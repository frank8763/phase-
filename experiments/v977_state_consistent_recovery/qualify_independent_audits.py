"""New saved-reference auditor positive and tampering/old-tracking negatives."""
import copy
import importlib.abc
import json
import sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v977_state_consistent_recovery'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('FORBIDDEN_MODEL_IMPORT '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import corridor_audit as audit
saved=json.loads((R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())
plans=json.loads((O/'ZERO_MODEL_QUALIFICATION.json').read_text())['rows']
checks={};proofs=[]
for index,plan in enumerate(plans):
    proof=audit.audit_reference(plan['plan'],saved['known'],saved['rows'][index]['search_source']['periodic'])
    checks['state'+str(index)+'_independent_full_cycle_reference']=proof['passed'];proofs.append(proof)
bad=copy.deepcopy(plans[0]['plan']);bad['state_path'][4][0]+=.01
try:audit.audit_reference(bad,saved['known'],saved['rows'][0]['search_source']['periodic'])
except AssertionError as error:checks['reference_tampering_rejected']=str(error)=='REFERENCE_NOT_RECONSTRUCTIBLE'
else:checks['reference_tampering_rejected']=False
with np.load(R/'runs/v976_saved_recovery_diagnosis/FIRST_SEGMENT_SAVED.npz')as data:
    original=audit.tracking(data['reference'],data['body'][:,:3],.0005)
checks['old_actual_heading_failure_still_rejected']=not original['passed']
report=dict(passed=all(checks.values()),checks=checks,proofs=proofs,original_actual_tracking=original,models=0,integrations=0,physical_authority=False)
(O/'INDEPENDENT_AUDITOR_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
