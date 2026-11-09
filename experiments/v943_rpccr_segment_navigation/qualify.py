"""Immutable science and integrated zero-model prerequisites before any vehicle."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v943_rpccr_segment_navigation';BASE=ROOT/'experiments/v934_rpccr_certified_recovery'
checks={}
for name in ['command_tube.py','cycle_backup.py','periodic_support.py','polygon_geometry.py','polygon_audit.py','motion_publisher.py','motion_audit.py','tube_audit.py','dynamic_proxy.py','A_motion.yaml','motion_bt.xml','reference_terminal.py','renewal_policy.py','packet_contract.py','repeat_contract.py','physical.py','certified_contract.py','native_contract.py','native_loop.py','ros_bridge.py','rpccr_recovery.py','ingress_audit.py','map_readiness.py']:
    old=(BASE/name).read_text().replace('v934_rpccr_certified_recovery','v943_rpccr_segment_navigation').replace('v934','v943').replace('V934','V943')
    checks['unchanged_'+name]=(CODE/name).read_text()==old
for name in ['supervise.py','watchdog.py']:
    checks['exact_qualified_'+name]=(CODE/name).read_bytes()==(ROOT/'experiments/v941_rpccr_reference_loss_binding'/name).read_bytes()
for source in CODE.glob('*.py'):ast.parse(source.read_text(),filename=str(source))
checks['all_python_ast']=True
names=['RECOVERY_SAVED_QUALIFICATION.json','RECOVERY_CALLBACK_QUALIFICATION.json','LOCAL_STOP_AUDIT_QUALIFICATION.json','NATIVE_SEAM_QUALIFICATION.json','INGRESS_QUALIFICATION.json','SEGMENT_QUALIFICATION.json','RPP_HANDOFF_QUALIFICATION.json','WATCHDOG_QUALIFICATION.json','SUPERVISOR_QUALIFICATION.json','CORRIDOR_AUDIT_QUALIFICATION.json']
for name in names:checks[name]=json.loads((OUT/name).read_text())['passed']
checks['prior18_platform_only_reused']=json.loads((OUT/'PRIOR_RESPONSE_QUALIFICATION.json').read_text())['all18_qualified']
checks['same_passed_rpp_parameters']=json.loads((CODE/'A_motion.yaml').read_text())['controller_server']['ros__parameters']['FollowPath']==json.loads((ROOT/'experiments/v884_feasible_rpp/A_feasible.yaml').read_text())['controller_server']['ros__parameters']['FollowPath']
checks['prior_physical_window_closed']=json.loads((ROOT/'runs/v934_rpccr_certified_recovery/COMPLETION.json').read_text())['closed']
checks['guard_unchanged']=hashlib.sha256((ROOT/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,
            scope='New reference-loss recovery supervisor only; existing nominal, command/native/sensor/model/threshold science unchanged. No physical outcome implied.')
(OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert report['passed']
