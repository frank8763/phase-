"""Verify reused scientific qualifications apply to unchanged scientific bytes."""
import ast,hashlib,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v920_native_ingress';P=R/'experiments/v918_reference_backup_balance'
names=['ros_bridge.py','ros_worker.py','physical.py','command_tube.py','periodic_support.py','cycle_backup.py','motion_publisher.py','motion_audit.py','tube_audit.py','dynamic_proxy.py','A_motion.yaml','motion_bt.xml','reference_terminal.py','renewal_policy.py','packet_contract.py','repeat_contract.py']
checks={}
for name in names:
 expected=(P/name).read_text().replace('v918_reference_backup_balance','v920_native_ingress').replace('v918','v920').replace('V918','V920')
 checks['unchanged_'+name]=(C/name).read_text()==expected
for name in ['CONDITIONAL_RESPONSE_QUALIFICATION.json','PLANNING_QUALIFICATION.json','AUDIT_QUALIFICATION.json','PRIOR_RESPONSE_QUALIFICATION.json']:
 d=json.loads((O/name).read_text());checks['old_qualified_'+name]=d.get('passed',d.get('all18_qualified',False))
for p in C.glob('*.py'):ast.parse(p.read_text())
for name in ['INGRESS_QUALIFICATION.json','INGRESS_AUDIT_QUALIFICATION.json','NATIVE_SEAM_QUALIFICATION.json']:checks[name]=json.loads((O/name).read_text())['passed']
checks['known_old_closed']=json.loads((R/'runs/v918_reference_backup_balance/COMPLETION.json').read_text())['closed']
report=dict(passed=all(checks.values()),checks=checks,new_models=0,integrations=0,reused_science_explicit=True,prior_version='V918',new_qualifications='14 ingress +14 execution/audit +6 native recording stub')
for name in ['ZERO_MODEL_QUALIFICATION.json','RELEASE_QUALIFICATION.json']:(O/name).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert report['passed']
