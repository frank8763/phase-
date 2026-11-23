"""Once two-NS overnight relay; scientific work stays in original exclusive owner."""
import fcntl,hashlib,json,os,selectors,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;ROOT=R/'runs/v1643_formal_parent_metadata';BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def alive(i):
 p=Path('/proc',str(i['pid']),'stat');return BOOT==i['boot_id']and p.exists()and p.read_text().split()[21]==i['start_ticks']
def stop(i):
 if alive(i):
  os.killpg(i['pgid'],signal.SIGTERM);until=time.monotonic()+15
  while alive(i)and time.monotonic()<until:time.sleep(.1)
  if alive(i):os.killpg(i['pgid'],signal.SIGKILL)
def command(args,label,timeout,deadline):
 start=time.monotonic();wall=time.time();buf=bytearray();p=subprocess.Popen([sys.executable,*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
 ident=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split()[21],boot_id=BOOT,args=args);put(D/(label+'_OWNED.json'),ident)
 try:
  sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);last=0
  while sel.get_map():
   assert time.time()<min(deadline,wall+timeout)and time.monotonic()<start+timeout and BOOT==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'OVERNIGHT_STAGE_CLOCK_STOP'
   if time.monotonic()-last>10:put(D/'CHECKPOINT.json',dict(unix=time.time(),stage=label,owned=ident,elapsed_s=time.monotonic()-start,concrete_work='existing single original owner or its full remote evidence closure; no duplicate',models_authorized_only_in_round_admission=True));last=time.monotonic()
   for key,_ in sel.select(.2):
    block=os.read(key.fileobj.fileno(),16384)
    if not block:sel.unregister(key.fileobj);continue
    assert len(buf)+len(block)<=1024**2,'NIGHT_CONSOLE_CAP';buf.extend(block)
  p.wait(timeout=5)
 finally:
  if p.poll()is None:stop(ident)
  (D/(label+'.console')).write_bytes(buf);put(D/(label+'_EXIT.json'),dict(returncode=p.poll(),wall_s=time.monotonic()-start))
 assert p.returncode==0,'OVERNIGHT_CHILD_CLOSURE_FAILED:'+label

def review(aid,helper):
 O=ROOT/'rounds'/aid;b=read(O/'POST_ROUND_STORAGE_BARRIER.json');assert b['passed']
 for a,h in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/b[a])==b[h]
 c=read(O/'COMPLETION.json');r=read(O/'actual/RESULT.json');closed=read(O/'RUNTIME_CLOSED_REVIEW.json')
 assert c['closed']and c['review_restored']and c['lock_idle']and c['all_source_SHA_verified_after_child_exit']and c['first_error']is None and not c['secondary_errors'],'OUTER_OR_SOURCE_ANOMALY'
 assert sha(O/'actual/RESULT.json')==c['machine_result_sha256']and not r['secondary_errors']and not r.get('model_native_inflight_unknown',False),'EVIDENCE_ANOMALY'
 assert r['evidence_saved']and(r.get('replay')or{}).get('passed')and r['new_actual_native']==r['own_replay_native']and r['fully_recorded_native']==r['new_actual_native'],'INCOMPLETE_CAPTURE_REPLAY'
 p=read(O/'actual/RESULT.json')['physical'];assert p['bad_contacts']==0 and p['minimum_actual_clearance_m']>=.15 and p['minimum_self_margin_m']>=0,'PHYSICAL_SAFETY_ANOMALY'
 if r['passed']:assert closed['independent_full_goal_audit']['passed']and r['actual_original_goal_reached']and r['first_error']is None
 else:
  assert(r.get('independent_prefix_audit')or{}).get('passed'),'PREFIX_SAFETY_UNREVIEWABLE'
  error=(r.get('first_error')or{}).get('error','');assert error in ["AssertionError('NO_CURRENT_WHOLE_GOAL_SOURCE')","AssertionError('EW_FRESH_DOMAIN_SOURCE_REFUSED')"],'UNCLASSIFIED_FAILURE_STOPS_NEXT'
 for path in [ROOT/'OWNER.lock',R/'runs/v648_static_unknown/execution.lock']:
  with path.open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for identity in [O/'OWNED_CHILD.json',R/'runs'/helper/'BACKGROUND_ONCE_CLAIM.json']:
  i=read(identity);assert not alive(i)
 return dict(assignment=aid,passed=r['passed'],actual_native=r['new_actual_native'],replay_native=r['own_replay_native'],canonical_barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'),all_original_safety_and_remote_closure_passed=True)

def main():
 os.sched_setaffinity(0,{5});auth=read(D/'AUTHORIZATION.json');assert auth['overnight_authorized']and time.time()<auth['no_new_model_launch_after_unix']
 assert not(D/'CONTROLLER_ONCE_CLAIM.json').exists()
 put(D/'CONTROLLER_ONCE_CLAIM.json',dict(pid=os.getpid(),pgid=os.getpgid(0),start_ticks=Path('/proc/self/stat').read_text().split()[21],boot_id=BOOT,started_unix=time.time(),authorization_sha256=sha(D/'AUTHORIZATION.json')))
 result=dict(closed=False,passed=False,models_launched_by_controller=0,rounds=[],next_stage='EW_EXACT_INPUT_RECOVERY_AND_ROUTE_SOURCE_PREPARATION',no_automatic_unqualified_EW=True);current_aid=None;helper=None
 try:
  for helper,current_aid in [('v1770_ns_phase07_night','phase_07__full'),('v1771_ns_phase08_night','phase_08__full')]:
   assert time.time()<auth['no_new_model_launch_after_unix']and time.time()+7200<auth['absolute_stop_unix'],'MORNING_LAUNCH_CUTOFF'
   N=R/'experiments'/helper;out=R/'runs'/helper;assert all(sha(R/n)==h for n,h in read(out/'HELPER_FREEZE.json')['files'].items())
   assert not(ROOT/'rounds'/current_aid/'ROUND_ONCE_CLAIM.json').exists(),'ALREADY_CLAIMED_NO_RETRY'
   cur=read(R/'CURRENT_EXPERIMENT.json');assert cur['active_round']is None and not cur['models_now_authorized'];cur.update(tonight_overnight_authorized=True,manual_review_after_every_round=False,automatic_next_round=True,active_overnight_campaign=str(D.relative_to(R)));put(R/'CURRENT_EXPERIMENT.json',cur)
   command([str(N/'prelaunch.py'),'--assignment',current_aid],current_aid+'_prelaunch',120,auth['absolute_stop_unix'])
   command([str(N/'background.py')],current_aid+'_runtime',7200,auth['absolute_stop_unix'])
   result['rounds'].append(review(current_aid,helper));put(D/'NS_PROGRESS.json',result)
  result.update(passed=True,waiting_for_agent_EW_prerequisites=True)
 except BaseException as e:
  result.update(first_error=repr(e),traceback=traceback.format_exc(),new_models_stopped=True,next_stage='SAFE_CLOSE_DIAGNOSIS_OR_PAPER_WORK_ONLY')
  if helper and current_aid:
   O=ROOT/'rounds'/current_aid
   for p in [O/'OWNED_CHILD.json',R/'runs'/helper/'live_io/owner_OWNED.json',R/'runs'/helper/'BACKGROUND_ONCE_CLAIM.json']:
    if p.exists():stop(read(p))
 finally:
  result.update(closed=True,closed_unix=time.time(),no_new_model_successor_from_this_controller=True);put(D/'NS_RELAY_RESULT.json',result)
  put(D/'CHECKPOINT.json',dict(unix=time.time(),stage=result['next_stage'],NS_relay_closed=True,NS_relay_passed=result['passed'],next_concrete_work='Continue exact EW prerequisite work and necessary source qualification; do not rerun NS. If unsafe, saved-data diagnosis and paper only.',overnight_stop_unix=auth['absolute_stop_unix']))
 print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
