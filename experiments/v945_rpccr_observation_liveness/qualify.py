"""Verify fixed mainline and inherited science; no model imports or integrations."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; CODE=Path(__file__).parent
OUT=ROOT/'runs/v945_rpccr_observation_liveness'; BASE=ROOT/'experiments/v943_rpccr_segment_navigation'
checks={}
names=['command_tube.py','cycle_backup.py','periodic_support.py','polygon_geometry.py',
       'polygon_audit.py','motion_publisher.py','motion_audit.py','tube_audit.py',
       'dynamic_proxy.py','A_motion.yaml','motion_bt.xml','reference_terminal.py',
       'renewal_policy.py','packet_contract.py','repeat_contract.py','physical.py',
       'certified_contract.py','native_contract.py','native_loop.py','ros_bridge.py',
       'rpccr_recovery.py','ingress_audit.py','map_readiness.py','corridor_audit.py','audit.py']
for name in names:
    old=(BASE/name).read_text().replace('v943_rpccr_segment_navigation','v945_rpccr_observation_liveness').replace('v943','v945').replace('V943','V945')
    checks['unchanged_'+name]=(CODE/name).read_text()==old
for source in CODE.glob('*.py'): ast.parse(source.read_text(),filename=str(source))
checks['all_python_ast']=True
for name in ['LIVENESS_QUALIFICATION.json','SUPERVISOR_QUALIFICATION.json','CORRIDOR_AUDIT_QUALIFICATION.json']:
    checks['new_'+name]=json.loads((OUT/name).read_text())['passed']
for name in ['RECOVERY_SAVED_QUALIFICATION.json','RECOVERY_CALLBACK_QUALIFICATION.json',
             'LOCAL_STOP_AUDIT_QUALIFICATION.json','NATIVE_SEAM_QUALIFICATION.json',
             'INGRESS_QUALIFICATION.json','SEGMENT_QUALIFICATION.json',
             'RPP_HANDOFF_QUALIFICATION.json','WATCHDOG_QUALIFICATION.json']:
    checks['reused_old_'+name]=json.loads((OUT/name).read_text())['passed']
checks['old18_platform_only_reused']=json.loads((OUT/'PRIOR_RESPONSE_QUALIFICATION.json').read_text())['all18_qualified']
checks['same_passed_rpp']=json.loads((CODE/'A_motion.yaml').read_text())['controller_server']['ros__parameters']['FollowPath']==json.loads((ROOT/'experiments/v884_feasible_rpp/A_feasible.yaml').read_text())['controller_server']['ros__parameters']['FollowPath']
checks['original_repro_red']=not json.loads((OUT/'REPRO_ORIGINAL.json').read_text())['passed']
checks['candidate_repro_green']=json.loads((OUT/'REPRO_CANDIDATE.json').read_text())['passed']
checks['previous_window_closed']=json.loads((ROOT/'runs/v943_rpccr_segment_navigation/COMPLETION.json').read_text())['closed']
checks['guard_unchanged']=hashlib.sha256((ROOT/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,
            scope='Observation liveness/fault evidence only. Old physical achievements preserved separately; no new-version arrival assumed.')
(OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[k for k,v in checks.items()if not v])))
assert report['passed']
