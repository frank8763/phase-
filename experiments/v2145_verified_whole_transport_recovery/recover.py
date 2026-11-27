"""Actual remote closure first, then exact whole-duplicate unlink only."""
from pathlib import Path
import fcntl,hashlib,json,os,signal,subprocess,time,traceback
from evidence import R,C,ROOT as S,read,put,sha,ref,deliver
from qualify import statrow
def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'RECOVERY_ONCE.json').exists();assert read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];frozen=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();left=read(S/'AUTHORIZATION.json')['absolute_end_unix']-time.time();assert 0<left<=5400;mono_end=time.monotonic()+left;signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('RECOVERY_ROOT_STOP')));signal.setitimer(signal.ITIMER_REAL,left);put(S/'RECOVERY_ONCE.json',dict(pid=os.getpid(),unix=time.time(),boot_id=boot,hard_stop_monotonic=mono_end,models=0));result=dict(passed=False,closed=False,models=0,physics=0,replay=0,removed=[],groups_closed=[])
 try:
  with(R/'runs/v648_static_unknown/execution.lock').open()as one,(R/'runs/v1643_formal_parent_metadata/OWNER.lock').open()as two:
   for lock in [one,two]:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   current=read(R/'CURRENT_EXPERIMENT.json');assert not current['models_now_authorized']and current.get('active_round')is None and sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
   for g in read(S/'PLAN.json')['groups']:
    assert time.time()<read(S/'AUTHORIZATION.json')['absolute_end_unix']-650 and time.monotonic()<mono_end-650 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot
    key=g['id'];D=S/'runtime_archives'/key;O=S/'components'/key;D.mkdir(parents=True);O.mkdir(parents=True);(D/'archive').mkdir()
    index=read(R/g['index_path']);assert sha(R/g['index_path'])==g['index_sha256'];parts=[]
    for old in g['parts']:
     name=key+'__'+old['name'];target=D/'archive'/name;assert sha(R/old['path'])==old['sha256'];os.link(R/old['path'],target);parts.append(dict(name=name,bytes=old['bytes'],sha256=old['sha256']))
    recovery=dict(index,parts=parts,original_archive_index=g['index_path'],original_archive_index_sha256=g['index_sha256'],transport_only=True)
    put(D/'ARCHIVE_INDEX.json',recovery);put(D/'FINALIZED.json',dict(passed=True,only_existing_archive_registered=True,scientific_navigation_passed=None,new_archive_or_models=False));put(O/'COMPLETION.json',dict(closed=True,scope='EXISTING_ARCHIVE_TRANSPORT_ONLY',scientific_navigation_passed=None,models=0))
    ref(key)
    # Separate bounded IO child; no global signal handlers or environment leaks.
    log=(O/'delivery.console').open('xb')
    try:p=subprocess.run(['taskset','-c','5','nice','-n','19','/usr/bin/python3','-B',str(C/'evidence.py'),'deliver',key],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=625)
    finally:log.close()
    assert p.returncode==0 and read(D/'FULL_REMOTE_VERIFIED.json')['passed']and read(D/'TRANSPORT_CLEANUP.json')['passed'],key
    row=g['whole_duplicate'];target=R/row['path'];assert statrow(target)==row;assert row['sha256']==read(D/'ARCHIVE_INDEX.json')['archive_sha256'];assert all(sha(R/z['path'])==z['sha256']for z in g['parts'])
    put(O/'WHOLE_DUPLICATE_CLEANUP_CLAIM.json',dict(entry=row,full_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),original_split_parts_preserved=True))
    target.unlink();result['removed'].append(row);result['groups_closed'].append(key);put(O/'WHOLE_DUPLICATE_CLEANUP.json',dict(passed=True,removed=row['path'],freed_allocated_bytes=row['allocated'],original_parts_and_raw_retained=True,models=0))
   assert all(sha(R/n)==h for n,h in frozen.items());result.update(passed=True,freed_allocated_bytes=sum(z['allocated']for z in result['removed']),all_current_frozen_source_SHA_unchanged=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc(),unverified_originals_retained=True)
 result.update(closed=True,models=0,finished_unix=time.time());put(S/'RESULT.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
