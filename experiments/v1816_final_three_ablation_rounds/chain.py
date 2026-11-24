"""Fixed8 EW overnight tasks, fully bounded script; no chat supervision."""
from pathlib import Path
import json,hashlib,importlib.util,os,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;NIGHT=R/'runs/v1769_overnight_phase_campaign';ROOT=R/'runs/v1643_formal_parent_metadata'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});auth=read(D/'AUTHORIZATION.json');assert auth['finite4_daytime']and not auth['overnight']
 with(D/'CHAIN_ONCE_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),unix=time.time(),automatic_chat_supervision=False),f)
 spec=importlib.util.spec_from_file_location('overnight_existing_safe_review',R/'experiments/v1769_overnight_phase_campaign/controller.py');review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
 result=dict(closed=False,rounds=[],passed=False,no_chat_supervision=True);aid=None
 try:
  for aid in auth['fixed_remaining_order']:
   assert time.time()+7200<auth['absolute_stop_unix'],'DAYTIME_BATCH_ADMISSION_DEADLINE'
   assert not(ROOT/'rounds'/aid/'ROUND_ONCE_CLAIM.json').exists(),'NO_DUPLICATE_ASSIGNMENT'
   helper=D/aid;helper.mkdir(exist_ok=True);put(helper/'USER_SINGLE_ROUND_COMMAND.json',dict(assignment=aid,overnight_authorization_path=str((NIGHT/'AUTHORIZATION.json').relative_to(R)),bounded_daytime_batch=True,no_manual_pause=True))
   cur=read(R/'CURRENT_EXPERIMENT.json');assert cur['active_round']is None and not cur['models_now_authorized'];cur.update(manual_review_after_every_round=True,automatic_next_round=False,active_source_round=None);put(R/'CURRENT_EXPERIMENT.json',cur)
   subprocess.run([sys.executable,str(C/'prelaunch.py'),'--assignment',aid],cwd=R,check=True,timeout=120)
   subprocess.run([sys.executable,str(C/'background.py'),'--assignment',aid],cwd=R,check=True,timeout=min(7200,auth['absolute_stop_unix']-time.time()))
   # Review exact canonical/source/physical/audit/replay/remote proofs from original shared function.
   review.read=lambda p:read(p)
   # Original reviewer needs the background claim path under each assignment.
   oldR=review.R
   O=ROOT/'rounds'/aid;b=read(O/'POST_ROUND_STORAGE_BARRIER.json');assert b['passed']
   for a,h in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/b[a])==b[h]
   m=read(O/'actual/RESULT.json');outer=read(O/'COMPLETION.json');assert outer['closed']and outer['review_restored']and outer['lock_idle']and outer['all_source_SHA_verified_after_child_exit']and outer['first_error']is None and not outer['secondary_errors']
   assert not m['secondary_errors']and m['evidence_saved']and(m.get('replay')or{}).get('passed')and not m.get('model_native_inflight_unknown',False)and m['fully_recorded_native']==m['new_actual_native']==m['own_replay_native']
   physical=m['physical'];assert physical['bad_contacts']==0 and physical['minimum_actual_clearance_m']>=.15 and physical['minimum_self_margin_m']>=0
   if m['passed']:assert(m.get('independent_audit')or{}).get('passed')and m['first_error']is None
   else:
    assert(m.get('independent_prefix_audit')or{}).get('passed')and(m.get('first_error')or{}).get('error')in ["AssertionError('NO_CURRENT_WHOLE_GOAL_SOURCE')","AssertionError('EW_FRESH_DOMAIN_SOURCE_REFUSED')","AssertionError('FIRST_DISCOVERY_NOT_NORMAL_DRIVING')"],'NON_SCIENTIFIC_OR_UNSAFE_FAILURE_STOPS'
   row=dict(assignment=aid,passed=m['passed'],actual_native=m['new_actual_native'],own_replay_native=m['own_replay_native'],barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'));result['rounds'].append(row);put(D/'CHAIN_PROGRESS.json',result)
  result['passed']=True
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc(),new_model_launches_stopped=True,failed_or_blocked_assignment=aid)
 finally:
  result.update(closed=True,closed_unix=time.time());put(D/'CHAIN_RESULT.json',result)
  cur=read(R/'CURRENT_EXPERIMENT.json');cur.update(automatic_next_round=False,manual_review_after_every_round=True,status='FINITE_ABLATION3_COMPLETE_WAITING_USER_REVIEW'if result['passed']else'FINITE_ABLATION3_STOPPED_EVIDENCE_REVIEW_REQUIRED',next_experiment='Await morning review of fixed remaining formal outcomes and paper materials; do not manufacture retries');put(R/'CURRENT_EXPERIMENT.json',cur)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
