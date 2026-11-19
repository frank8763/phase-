"""Re-run the unchanged independent audit, with no physical imports or writes."""
import copy
import hashlib
import importlib.abc
import json
import os
from pathlib import Path
import platform
import sys

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('ZERO_MODEL_AUDIT_IMPORT '+name)


sys.meta_path.insert(0,NoPhysical())
sys.path.insert(0,str(R/'experiments/v1368_rolling_map_entry'))
import audit as production
import numpy as np


def main():
    mode=sys.argv[1];assert mode in ['host','producer']
    os.sched_setaffinity(0,{3,4,5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    manifest=json.loads((C/'SOURCE_FREEZE.json').read_text())['files']
    assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in manifest.items())
    task=json.loads((R/'experiments/v1368_rolling_map_entry/TASKS.json').read_text())[0]
    out=Path(task['output']);events_file=out/'RESERVE_RECORDS.json';events=json.loads(events_file.read_text())
    original_read=production.read;ball=task['causal_ball'];differences=[]
    sys.path.insert(0,str(R/'experiments/v1361_dynamic_reserve_consistency'))
    from dynamic_reserve import check
    for i,event in enumerate(events):
        allowed,proof=check(event['body'],ball,*event['requested'])
        assert allowed==event['dynamic_allowed'],'DECISION_MISMATCH'
        for key,value in proof.items():
            if value!=event['dynamic_proof'][key]:
                assert isinstance(value,float) and isinstance(event['dynamic_proof'][key],float)
                differences.append(dict(index=i,field=key,recorded=event['dynamic_proof'][key],rebuilt=value,absolute_error=abs(value-event['dynamic_proof'][key])))
    audit=production.audit(task)
    if mode=='host':assert not audit['passed'] and {k for k,v in audit['checks'].items() if not v}=={'causal_field_guard_reconstructs'}
    else:assert audit['passed'] and differences==[],'PRODUCER_EXACT_AUDIT_FAILED'
    negatives=[]
    if mode=='producer':
        for name in ['decision','one_ulp_scalar','reason']:
            bad=copy.deepcopy(events)
            if name=='decision':bad[0]['dynamic_allowed']=not bad[0]['dynamic_allowed']
            elif name=='one_ulp_scalar':bad[0]['dynamic_proof']['current_dynamic_clearance_m']=float(np.nextafter(bad[0]['dynamic_proof']['current_dynamic_clearance_m'],np.inf))
            else:bad[0]['dynamic_proof']['reason']='FORGED_REASON'
            production.read=lambda p:copy.deepcopy(bad) if Path(p)==events_file else original_read(p)
            try:rejected=production.audit(task)
            finally:production.read=original_read
            assert not rejected['passed'] and not rejected['checks']['causal_field_guard_reconstructs'],'TAMPER_ACCEPTED'
            negatives.append(dict(tamper=name,rejected=True))
    assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in manifest.items())
    result=dict(closed=True,diagnosis_passed=True,supplemental_full_audit_passed=audit['passed'],audit=audit,
        guard_events=len(events),proof_differences=differences,maximum_proof_error=max((d['absolute_error'] for d in differences),default=0.),
        all_decisions_exact=True,tamper_negatives=negatives,python=platform.python_version(),numpy=np.__version__,
        interpreter=sys.executable,exact_proof_equality_required=True,safety_thresholds_unchanged=True,
        original_failed_audit_and_batch_unchanged=True,unexecuted=['rpp_recovery_repeat','mppi_recovery_main','mppi_recovery_repeat'],
        new_models=0,new_physical_native=0,new_replay_native=0,training_updates=0,source_unchanged=True)
    (O/(mode.upper()+'_AUDIT.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['diagnosis_passed','supplemental_full_audit_passed','guard_events','maximum_proof_error','all_decisions_exact','python','numpy','new_models','new_physical_native']}))


if __name__=='__main__':main()
