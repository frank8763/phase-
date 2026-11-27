"""Actual Phase namespace and prospective authority denials, zero model calls."""
import os,subprocess,json,ast,traceback
from context import R,C,SOURCE as S,load,put,read,sha
UNCHANGED=['response.py','error_stop.py','capture.py','runtime_binding.py','history_binding.py','work.py','work_budget.py','resource_policy.py','quota.py','base_quota.py','granted_quota.py','compact_json.py','evidence_service.py','direct_bits.py','audit_budget.py','generic_audit.py','observation.py','thread_observation.py','cpu_policy.py','input_frame.py']
def main():
 assert os.sched_getaffinity(0)=={4};out=S/'software';out.mkdir();result=dict(passed=False,closed=False,models=0,actual_renderers=0,policy_calls=0,optimizer_queries=0,physics=0,replay=0)
 try:
  ns=load('SCCR_actual_Phase_namespace',C/'run_phase.py');cmd=ns.namespace(C/'software_probe.py',out)
  p=subprocess.run(['taskset','-c','4',*cmd],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PHASE_FILTER_METHOD='SCCR',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),capture_output=True,timeout=30)
  assert p.returncode==0,p.stderr.decode()[-3000:];proof=json.loads(p.stdout);put(out/'PRODUCTION_SEAM.json',proof)
  denials=[]
  for n in ['pilot_entry.py','run_phase.py']:
   q=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(C/n)],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PHASE_FILTER_METHOD='SCCR',PYTHONDONTWRITEBYTECODE='1'),capture_output=True,timeout=5);assert q.returncode!=0 and b'NOT_ADMITTED'in q.stderr,n;denials.append(n)
  for n in UNCHANGED:assert(C/n).read_bytes()==(R/'experiments/v2141_pcbf_progress_scope'/n).read_bytes(),n
  for p in C.glob('*.py'):ast.parse(p.read_text())
  from evidence import deliver
  for rid in [None,'SCCR']:compile(deliver(rid,preview=True),str(C/'generated_transport.py'),'exec')
  result.update(passed=True,production_seam=proof,unadmitted_entries_refused=denials,unchanged_original_physical_modules=UNCHANGED,source_and_runtime_transport_preview_correct_scope=True)
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
 result['closed']=True;put(S/'COMPONENT_INTERFACE_PROOF.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
