"""Closed V943 partial-execution and freshness-boundary diagnosis; zero models."""
import copy
import gzip
import hashlib
import importlib.abc
import json
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/v944_rpccr_segment_postmortem'
RAW=ROOT/'runs/v858_nav2_verified/v943/main_we'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','torch','vehicle','factory','physical','rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
sys.path[:0]=[str(ROOT/'experiments/v943_rpccr_segment_navigation'),
              str(ROOT/'experiments/v938_rpccr_recovery_segments')]
from corridor_audit import body_rows,tracking
from transaction import RecoveryTransaction,fingerprint
from cycle_backup import retained_allowed


def read(path):return json.loads(path.read_text())


def main():
    OUT.mkdir(exist_ok=False)
    assert read(ROOT/'runs/v943_rpccr_segment_navigation/COMPLETION.json')['closed']
    row=read(RAW/'RECOVERY_CORRIDORS.json')[0]
    native=read(RAW/'RESULT.json');ros=read(RAW/'ROS_RESULT.json');audit=read(RAW/'INDEPENDENT_AUDIT.json')
    tubes=json.loads(gzip.decompress((RAW/'COMMAND_TUBES.json.gz').read_bytes()))
    with np.load(RAW/'physics/NATIVE_TRACE.npz') as trace:
        recorded=body_rows(trace)
    start=row['install_packet']['native_tick'];end=len(recorded)
    partial=tracking(row['proposal']['path'],recorded[start-1:end])
    goal=np.array([4.,-2.]);initial=np.array(row['entry_packet']['body'][:2]);final=recorded[-1,:2]
    installed=recorded[start-1,:2]
    retained=tubes[-1]['proof']
    fixture=[]
    for age in [.049,.050,.050001,.051,.1,.199,.201]:
        m=RecoveryTransaction([4.,-2.],read(RAW/'physics/SETUP.json')['known'])
        m.mode='FOLLOW_RECOVERY';m.path=copy.deepcopy(row['proposal']['path']);m.path_sha256=fingerprint(m.path)
        p=copy.deepcopy(tubes[-1]['packet']);s=copy.deepcopy(tubes[-1]['source'])
        # Deliberately synthetic age injection, not the unsaved actual failing snapshot.
        now=p['body_measured_at']+age;s['decision_at']=now;s['source_age_s']=.01
        m.installed_at=now-1.
        try:m.monitor(p,s,now);error=None
        except AssertionError as e:error=str(e)
        fixture.append(dict(synthetic_body_age_s=age,monitor_error=error,
                            original_retained_permission_valid=retained_allowed(retained,age),
                            command_50ms_admission_is_not_relaxed=True))
    assert fixture[0]['monitor_error'] is None
    assert all(x['monitor_error']=='STALE_BODY' for x in fixture[2:])
    result=dict(models=0,integrations=0,original_batch_status='NOT_PASSED',
                trigger_tick=row['entry_packet']['native_tick'],install_tick=start,
                actual_new_reference_installed=True,completed_recovery_segments=0,
                recovered_prefix_actual_native=end-start+1,
                partial_recovery_tracking=partial,
                actual_displacement_after_install_m=float(np.linalg.norm(final-installed)),
                actual_goal_improvement_from_recovery_entry_m=float(np.linalg.norm(initial-goal)-np.linalg.norm(final-goal)),
                actual_distance_to_segment_endpoint_m=float(np.linalg.norm(final-row['proposal']['path'][-1][:2])),
                final_original_goal_distance_m=native['goal_distance_m'],
                evidence_passed=audit['evidence_passed'],functional_passed=audit['functional_passed'],
                minimum_actual_clearance_m=audit['minimum_clearance_m'],bad_contacts=audit['bad_contacts'],
                actual_native=native['actual_native'],own_replay_native=native['replay_native'],private_native=native['private_native'],
                state_replay_max_error=audit['maximum_state_error'],
                error=ros['error'],error_site='RecoveryTransaction.monitor -> fresh <=50ms body-age guard',
                actual_failing_snapshot_or_precise_body_age_saved=False,
                exact_failure_age_s=None,
                freshness_boundary_fixture=fixture,
                source_scope='Original source unchanged; synthetic age fixtures do not prove the unrecorded exact delay or counterfactual arrival.',
                next_revision_spec=['Keep original50ms new-command and installation admission unchanged.',
                                    'Separate <=200ms supervisory observation liveness from fresh-command issuance; a short delay only permits retaining an already qualified immutable proof, never a stale new command or clock reset.',
                                    'Beyond original source-liveness/permission bounds stop; independently test51/100/199/201ms boundaries and old-proof expiry.',
                                    'Persist the exact fault packet/source/time and partial transaction events before raising.',
                                    'No patch, model restart or additional candidate in this closed window.'])
    (OUT/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='freshness_boundary_fixture'},indent=2))
    assert partial['passed'],'PARTIAL_REFERENCE_TRACKING_NOT_QUALIFIED'


if __name__=='__main__':main()
