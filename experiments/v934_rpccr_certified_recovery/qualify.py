"""Pre-model exact scientific diff and required integrated qualifications."""
import ast,hashlib,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v934_rpccr_certified_recovery';P=R/'experiments/v924_consistent_polygon_reference'
checks={}
for name in ['command_tube.py','cycle_backup.py','periodic_support.py','polygon_geometry.py','polygon_audit.py','motion_publisher.py','motion_audit.py','tube_audit.py','dynamic_proxy.py','A_motion.yaml','motion_bt.xml','reference_terminal.py','renewal_policy.py','packet_contract.py','repeat_contract.py','physical.py','certified_contract.py','supervise.py']:
 expected=(P/name).read_text().replace('v924_consistent_polygon_reference','v934_rpccr_certified_recovery').replace('v924','v934').replace('V924','V934');checks['unchanged_'+name]=(C/name).read_text()==expected
for p in C.glob('*.py'):ast.parse(p.read_text())
checks['all_python_ast']=True
for name in ['RECOVERY_SAVED_QUALIFICATION.json','RECOVERY_CALLBACK_QUALIFICATION.json','NATIVE_SEAM_QUALIFICATION.json','INGRESS_QUALIFICATION.json','LOCAL_STOP_AUDIT_QUALIFICATION.json']:
 checks[name]=json.loads((O/name).read_text())['passed']
a=json.loads((R/'experiments/v884_feasible_rpp/A_feasible.yaml').read_text())['controller_server']['ros__parameters']['FollowPath'];b=json.loads((C/'A_motion.yaml').read_text())['controller_server']['ros__parameters']['FollowPath'];checks['same_passed_rpp_controller_parameters']=a==b
checks['old18_response_qualified']=json.loads((O/'PRIOR_RESPONSE_QUALIFICATION.json').read_text())['all18_qualified']
checks['old_dynamic_batch_closed']=json.loads((R/'runs/v924_consistent_polygon_reference/COMPLETION.json').read_text())['closed']
checks['mppi_branch_excluded']=not any('mppi'in p.read_text().lower()for p in [C/'ros_bridge.py',C/'A_motion.yaml',C/'rpccr_recovery.py'])
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,static_anchor='V884/V885 same FollowPath, no new static acceptance claim',changed_science='Certified alternative arbitration only; command_tube/threshold/cycle/causal motion/controller all exact previous bytes')
(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
