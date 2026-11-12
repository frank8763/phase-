"""Supplemental zero-model audit; original frozen failed audit stays unchanged."""
import sys,json,time,signal,hashlib,traceback,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1085_audit_entry_diagnosis';ORIGINAL=R/'experiments/rpccr_execution_core/fresh_audit.py'
OLD="p['body'][:3]==task['start_xy']+[task['start_yaw']]"
# Build the balanced expression explicitly; no other scientific expression changes.
NEW="np.max(np.abs(np.asarray(p['body'][:3])-np.asarray(task['start_xy']+[task['start_yaw']])))<=1e-8"
OUT_OLD="dump(out/'FINAL_INDEPENDENT_AUDIT.json',answer)"
OUT_NEW="dump(Path(DIAG_OUTPUT)/'SUPPLEMENTAL_INDEPENDENT_AUDIT.json',answer)"
def patched_source():
 source=ORIGINAL.read_text();assert source.count(OLD)==source.count(OUT_OLD)==1
 patched=source.replace(OLD,NEW).replace(OUT_OLD,OUT_NEW);assert patched.replace(NEW,OLD).replace(OUT_NEW,OUT_OLD)==source
 return patched

def main():
 assert not(O/'AUDIT_CLAIM.json').exists();(O/'AUDIT_CLAIM.json').write_text(json.dumps(dict(started_unix=time.time(),original_audit_sha256=hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),scientific_change='Only original1e-8 t0 pose tolerance; reporting routed to supplemental directory',models=0,integrations=0),indent=2)+'\n')
 def halt(*_):raise TimeoutError('BOUNDED_ZERO_MODEL_AUDIT')
 signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,900);started=time.monotonic()
 try:
  module=types.ModuleType('v1085_supplemental_saved_audit');module.__file__=str(ORIGINAL);module.DIAG_OUTPUT=str(O);exec(compile(patched_source(),str(ORIGINAL),'exec'),module.__dict__);task=json.loads((O/'TASK.json').read_text());answer=module.audit(task);record=dict(closed=True,passed=answer['passed'],audit=answer,original_batch_failed_unchanged=True,repeat_not_executed=True,diagnostic_wall_s=time.monotonic()-started,models=0,integrations=0)
 except BaseException as e:record=dict(closed=True,passed=False,error=repr(e),traceback=traceback.format_exc(),original_batch_failed_unchanged=True,diagnostic_wall_s=time.monotonic()-started,models=0,integrations=0)
 finally:signal.setitimer(signal.ITIMER_REAL,0)
 (O/'COMPLETION.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
if __name__=='__main__':main()
