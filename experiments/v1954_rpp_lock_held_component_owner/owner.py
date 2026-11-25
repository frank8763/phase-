"""Metadata-only wrapper: exact original owner, lifetime-held model lock."""
from context import R,C,O,read,sha,put,load
import fcntl,json,os,subprocess,sys,traceback,time
TARGET=R/'experiments/v1952_rpp_component_entry_checked';OUTPUT=R/'runs/v1952_rpp_component_entry_checked'
def main():
 assert not(O/'ACTUAL_ONCE_CLAIM.json').exists()and not(OUTPUT/'COMPONENT_OUTER_ONCE_CLAIM.json').exists()and not(OUTPUT/'RESULT.json').exists()
 freeze=read(O/'SOURCE_FREEZE.json');assert all(sha(R/n)==h for n,h in freeze['files'].items());rec=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert rec['passed']and rec['all_frozen_members_remote_chain_covered']and read(O/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];assert read(OUTPUT/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 put(O/'ACTUAL_ONCE_CLAIM.json',dict(unix=time.time(),pid=os.getpid(),original_owner_sha256=sha(TARGET/'owner.py'),wrapper_source_recovery_sha256=sha(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json'),one_original_component=True));os.sched_setaffinity(0,{5});os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 expected=['taskset','-c','2','nice','-n','19','ionice','-c','3','./run_phase.sh',str((TARGET/'entry.py').relative_to(R))];popen=subprocess.Popen;calls=[];oldcontext=sys.modules.get('context');original=None
 def locked_child(args,*a,**kw):
  assert args==expected and not calls,'UNEXPECTED_OR_DUPLICATE_NUMERICAL_LAUNCH';calls.append(1);args=['flock','-n',str(R/'runs/v648_static_unknown/execution.lock'),*args];put(O/'EXACT_LOCKED_ARGV.json',dict(argv=args,original_owner_sha256=sha(TARGET/'owner.py'),original_entry_sha256=sha(TARGET/'entry.py'),lifetime_lock_until_child_exit=True,metadata_only_argv_prefix=True));return popen(args,*a,**kw)
 result=dict(passed=False,closed=False,models=0,physics=0,replay=0)
 try:
  ownercontext=load('component_scoped_original_context',TARGET/'context.py');sys.modules['context']=ownercontext;original=load('original_rpp_component_owner',TARGET/'owner.py');code=original.main.__code__;subprocess.Popen=locked_child;rc=original.main();assert original.main.__code__ is code;assert len(calls)==1;result.update(passed=rc==0,original_owner_returncode=rc,original_functioncode_unchanged=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  subprocess.Popen=popen
  if oldcontext is not None:sys.modules['context']=oldcontext
  result.update(closed=True,child_launches=len(calls),all_wrapper_source_after_exit_SHA_verified=all(sha(R/n)==h for n,h in freeze['files'].items()));put(O/'COMPONENT_OWNER_CLOSED.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
