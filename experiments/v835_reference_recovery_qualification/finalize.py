"""Persisted component audit/archive only; never retries a physical probe."""
import fcntl,subprocess,sys
from helpers import *
sys.path.insert(0,str(repo/'experiments/reference_recovery_20261106'))
from archive import archive
lock=(root/'finalize.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if(root/'FINALIZED.json').exists():print('ALREADY_FINALIZED_NO_OVERWRITE');raise SystemExit(0)
assert read(root/'ROUND_WINDOW.json')['round_closed']and(repo/'REVIEW_PENDING').exists()
passed=False;audit=None
if(root/'RESULT.json').exists():
 with(root/'audit_saved.console').open('x')as stream:p=subprocess.run([sys.executable,'-B',str(own/'audit_saved.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=300)
 if p.returncode==0:
  audit=read(root/'FINAL_INDEPENDENT_AUDIT.json');passed=audit['component_passed']
 else:
  audit=dict(status='INDEPENDENT_AUDIT_FAILED',component_passed=False,independent_audit_exit=p.returncode,counts=read(root/'COMPLETION.json')['counts'],evidence_retained=True,new_models=0,new_integrations=0);dump(root/'FAILED_INDEPENDENT_AUDIT.json',audit)
else:
 audit=dict(status='COMPONENT_INTERRUPTED_NOT_QUALIFIED',component_passed=False,counts=read(root/'COMPLETION.json')['counts'],evidence_retained=True,new_models=0,new_integrations=0);dump(root/'FAILED_INDEPENDENT_AUDIT.json',audit)
report=repo/'docs/RPCCR_REFERENCE_RECOVERY_V835_REPORT.md';report.write_text('# 固定返回逃离完整尾资格\n\n状态：'+('PASS'if passed else'NOT_PASSED')+'。\n\n'+json.dumps(audit or read(root/'COMPLETION.json'),ensure_ascii=False,indent=2)+'\n\n固定490/495、旧3960重放、新完整336分支（原328+8接续）与完整重复分别记账。这里只是组件，不是完整导航/新24验收。所有旧失败保持；原完整安全门不减，原始证据保留。\n')
saved=archive(repo,root,own,report,own/'INPUT_FREEZE.json','evidence/rpccr_reference_recovery_v835_20261106');dump(root/'FINALIZED.json',dict(status='FIXED_ESCAPE_COMPONENT_VERIFIED'if passed else'NOT_PASSED',component_passed=passed,report=str(report.relative_to(repo)),**saved,new_models=0,new_integrations=0));print(json.dumps(read(root/'FINALIZED.json')))
