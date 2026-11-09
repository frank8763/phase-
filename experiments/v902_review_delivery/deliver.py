"""Closed evidence only: one new source push, Release restore, manifest-limited cleanup."""
import fcntl,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys,tarfile,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2]; C=Path(__file__).resolve().parent
O=R/'runs/v902_review_delivery'; REC=R/'records/dynamic_review_20261109'
GH=R/'tools/phase_storage_20261107/vendor/gh'; REPO='frank8763/phase-'; TAG='phase-dynamic-review-20261109'
BATCHES=[('runs/v896_overnight_20261108','records/nav2_overnight_20261108'),('runs/v900_refuge_terminal_set','records/nav2_v900_20261109'),('runs/v901_arm_ack_continuation','records/nav2_v901_20261109'),('runs/v903_retained_exit_reference','records/nav2_v903_20261109'),('runs/v905_reference_execution_separation','records/nav2_v905_20261109'),('runs/v907_recovery_corridor_memory','records/nav2_v907_20261109')]
NAMES=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/DYNAMIC_REVIEW_AND_PAPER_RECOVERY_20261109.md','docs/paper_ras/MANUSCRIPT_WORKING.md','docs/paper_ras/EVALUATION_GATES_20261109.md','docs/NAV2_REFUGE_OVERNIGHT_20261108_REPORT.md','docs/NAV2_REFUGE_TERMINAL_SET_V900_REPORT.md','docs/NAV2_REFUGE_TERMINAL_SET_V901_REPORT.md','experiments/v900_refuge_terminal_set','experiments/v901_arm_ack_continuation','experiments/v902_review_delivery','records/nav2_overnight_20261108','records/nav2_v900_20261109','records/nav2_v901_20261109','records/dynamic_review_20261109','experiments/v903_retained_exit_reference','docs/NAV2_REFUGE_TERMINAL_SET_V903_REPORT.md','records/nav2_v903_20261109','experiments/v904_reference_map_qualification','experiments/v905_reference_execution_separation','docs/NAV2_REFUGE_TERMINAL_SET_V905_REPORT.md','records/nav2_v904_20261109','records/nav2_v905_20261109','docs/paper_ras/figures/dynamic_failure_geometry_20261109.png','docs/paper_ras/figures/dynamic_recovery_cycle_20261109.png','experiments/v906_search_resolution_diagnosis','experiments/v907_recovery_corridor_memory','experiments/v908_causal_progress_contract','docs/NAV2_REFUGE_TERMINAL_SET_V907_REPORT.md','records/nav2_v907_20261109','records/nav2_v908_20261109']
def read(p):return json.loads(p.read_text())
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def command(args,timeout=30):return subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=timeout)
def gh(args,timeout=30):
    p=command([str(GH),*args],timeout)
    if p.returncode:raise RuntimeError('GH_FAILED '+args[0]+' '+p.stderr[-600:])
    return p.stdout
def closed_lock():
    for root,_ in BATCHES:
        assert read(R/root/'COMPLETION.json')['closed']
        assert read(R/root/'FINALIZED.json')['all_archive_source_and_decompressed_sha_verified']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    return lock
def prepare():
    lock=closed_lock();O.mkdir(exist_ok=True);REC.mkdir(exist_ok=True)
    assert not(O/'RECORD_INDEX.json').exists(),'ALREADY_PREPARED_NO_OVERWRITE'
    spec=importlib.util.spec_from_file_location('review_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=False)
    files=[]
    for name in NAMES:
        p=R/name
        if p.is_dir():files.extend(m.walk(p))
        elif p.is_file():files.append(p)
    files.extend(m.walk(R/'runs/v908_causal_progress_contract'))
    for root,_ in BATCHES:
        files.extend(p for p in m.walk(R/root) if 'cloud' not in p.relative_to(R/root).parts and 'audit_fixture' not in p.relative_to(R/root).parts)
    supplement=m.archive('review-closed-operations-20261109',files)
    groups=[]
    for root,record in BATCHES:
        index=read(R/record/'RECORD_INDEX.json')
        for group in index['archives']:groups.append(dict(group,local_cloud=str(Path(root)/'cloud')))
    groups.append(dict({k:v for k,v in supplement.items()if k!='files'},local_cloud=str(m.OUT.relative_to(R))))
    index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',archives=groups,old_v897_source_push_not_retried=True,scope='All six closed runtime evidence archives plus current review and closure snapshots')
    dump(O/'RECORD_INDEX.json',index);dump(REC/'RECORD_INDEX.json',index)
    print('PREPARED',flush=True)
def deliver():
    lock=closed_lock();assert not(O/'DELIVERY_CLAIM.json').exists()
    with(O/'DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),pid=os.getpid(),models=0,no_retry=True),f)
    result=dict(status='PENDING',models=0,integrations=0,raw_deleted=False,old_v897_push_retried=False)
    try:
        index=read(O/'RECORD_INDEX.json');staged=command(['git','diff','--cached','--name-only']).stdout.splitlines()
        assert staged and all(any(n==p or n.startswith(p+'/')for p in NAMES)for n in staged),'UNRELATED_STAGED_FILES'
        assert all((R/n).is_file()and not(R/n).is_symlink()and(R/n).stat().st_size<90*1024**2 for n in staged)
        p=command(['git','diff','--cached','--check']);assert p.returncode==0,p.stdout
        (O/'SOURCE_REVIEW.console').write_text(command(['git','diff','--cached','--stat']).stdout)
        p=command(['git','commit','-m','Diagnose dynamic recovery, validate terminal-set development, and update paper evidence'],30);assert p.returncode==0,p.stderr
        head=command(['git','rev-parse','HEAD']).stdout.strip();result['source_commit']=head
        assert command(['git','remote','get-url','origin']).stdout.strip()=='https://github.com/frank8763/phase-.git'
        sync=dict(source_commit=head,push_budget_s=30,read_budget_s=5,attempted_once=True)
        with(O/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
        try:
            p=command(['git','push','origin','main'],30);sync.update(push_returncode=p.returncode,push_succeeded=p.returncode==0);(O/'push.console').write_text(p.stdout+p.stderr)
        except subprocess.TimeoutExpired:sync['push_error']='30S_TIMEOUT_NO_RETRY'
        try:
            p=command(['git','ls-remote','origin','refs/heads/main'],5);remote=p.stdout.split()[0]if p.returncode==0 and p.stdout.strip()else None;sync.update(remote_head=remote,remote_head_verified=remote==head)
        except subprocess.TimeoutExpired:sync['read_error']='5S_TIMEOUT_NO_RETRY'
        dump(O/'GIT_SYNC_RESULT.json',sync);dump(REC/'GIT_SYNC_RESULT.json',sync)
        assert sync.get('remote_head_verified'),'SOURCE_REMOTE_UNVERIFIED_PRESERVE_RAW'
        print('SOURCE_REMOTE_VERIFIED',flush=True)
        body='Phase dynamic review 2026-11-09: preserves V897 temporary-goal timeout and V900 stale ARM-ack entry failure; V901 is one operational continuation with unchanged V900 terminal-region science and original deadline, which failed because the newly planned exit differs from the admitted historical path. V903 evaluates retaining that same actual-history exit reference but fails earlier in original-route planning. V904 saved real Nav2 probes isolate hard dynamic reference occupancy; V905 evaluates soft global risk versus unchanged hard local execution. V907 preserves causal corridor memory but still cycles through three recoveries and fails, with one10ms pose/scan provenance mismatch. V908 is zero-model atomic snapshot and terminal-contract preparation, not a qualified navigation. Per-batch reports contain the actual outcomes. Includes complete original runtime evidence, causal sensors, controls, own replays, audit results and current paper-gap review. No new24 confirmation, algorithm superiority, formal recursive-safety or real-robot claim. Old V897 source push is not retried.'
        release=json.loads(gh(['api',f'repos/{REPO}/releases','--method','POST','-f','tag_name='+TAG,'-f','target_commitish='+head,'-F','draft=true','-f','name=Phase dynamic review and terminal-region development 2026-11-09','-f','body='+body]))
        dump(O/'RELEASE_CREATED.json',dict(id=release['id'],tag_name=TAG))
        items=[O/'RECORD_INDEX.json']
        for g in index['archives']:
            cloud=R/g['local_cloud'];items.extend([cloud/(g['group']+'.INVENTORY.json'),*[cloud/p['name']for p in g['parts']]])
        assert len({p.name for p in items})==len(items),'ASSET_NAME_COLLISION'
        gh(['release','upload',TAG,*map(str,items),'--repo',REPO],180)
        assets=json.loads(gh(['api',f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100'],15));by_name={a['name']:a for a in assets}
        for p in items:assert by_name[p.name]['size']==p.stat().st_size and by_name[p.name].get('digest')=='sha256:'+sha(p),p.name
        cache=O/'remote_restore';cache.mkdir(exist_ok=False);gh(['release','download',TAG,'--repo',REPO,'--dir',str(cache)],180)
        for p in items:assert sha(cache/p.name)==sha(p),p.name
        restored=0;originals={}
        for g in index['archives']:
            inventory=read(cache/(g['group']+'.INVENTORY.json'));expected={x['path']:x for x in inventory['files']};originals.update(expected)
            archive=cache/'joined.tar.zst'
            with archive.open('xb')as f:
                for part in g['parts']:
                    with(cache/part['name']).open('rb')as source:shutil.copyfileobj(source,f)
            assert sha(archive)==g['archive_sha256'];proc=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE);seen=set()
            try:
                with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
                    for member in tf:
                        name=Path(member.name);assert not name.is_absolute()and '..'not in name.parts and member.name not in seen
                        row=expected[member.name];assert member.isfile()and row['type']=='file'and member.size==row['bytes'];seen.add(member.name)
                        target=cache/'one_member'
                        with target.open('xb')as f:shutil.copyfileobj(tf.extractfile(member),f)
                        assert sha(target)==row['sha256'];target.unlink();restored+=1
                assert proc.wait(timeout=20)==0 and seen==set(expected)
            finally:
                if proc.poll()is None:proc.kill();proc.wait()
            archive.unlink()
        gh(['release','edit',TAG,'--repo',REPO,'--draft=false'])
        proof=dict(passed=True,source_commit=head,actual_members_restored=restored,assets=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p))for p in items],release_url=index['release_url'],at=time.time())
        dump(REC/'REMOTE_VERIFIED.json',proof);result.update(remote_verified=True,actual_members_restored=restored,release_url=index['release_url']);print('ALL_REMOTE_MEMBERS_RESTORED '+str(restored),flush=True)
        frozen=set()
        for name in ['v897_refuge_navigation','v900_refuge_terminal_set','v901_arm_ack_continuation','v903_retained_exit_reference','v905_reference_execution_separation','v907_recovery_corridor_memory']:frozen.update(read(R/'experiments'/name/'SOURCE_FREEZE.json')['files'])
        bases=[R/'runs/v858_nav2_verified'/n for n in ['v897','v898_platform','v900','v901','v903','v905','v907']]+[R/'runs/v900_refuge_terminal_set/audit_fixture',R/'runs/v904_reference_map_qualification',R/'runs/v906_search_resolution_diagnosis',R/'runs/v907_recovery_corridor_memory/counterfactual_audit_fixture',R/'runs/v908_causal_progress_contract/joint_contract_probe']
        entries=[]
        for base in bases:
            if not base.exists():continue
            assert not base.is_symlink() and base.resolve().is_relative_to(R/'runs')
            for p in base.rglob('*'):
                rel=str(p.relative_to(R))
                if rel in frozen:continue
                if p.is_symlink():entries.append(dict(path=rel,type='symlink',link=os.readlink(p),bytes=p.lstat().st_size))
                elif p.is_file():
                    assert rel in originals and sha(p)==originals[rel]['sha256'],rel
                    entries.append(dict(path=rel,type='file',sha256=sha(p),bytes=p.stat().st_size))
        dump(REC/'CLEANUP_PLAN.json',dict(files=entries,frozen_sources_retained=True,remote_verified=True))
        for e in entries:
            p=R/e['path']
            if e['type']=='symlink':assert p.is_symlink()and os.readlink(p)==e['link']
            else:assert not p.is_symlink()and sha(p)==e['sha256']
            p.unlink()
        for base in bases:
            if not base.exists():continue
            for p in sorted([x for x in base.rglob('*')if x.is_dir()and not x.is_symlink()],key=lambda p:len(p.parts),reverse=True):
                if not any(p.iterdir()):p.rmdir()
            if not any(base.iterdir()):base.rmdir()
        for cloud in {R/g['local_cloud']for g in index['archives']}:
            assert cloud.resolve().is_relative_to(R/'runs')and not cloud.is_symlink();shutil.rmtree(cloud)
        shutil.rmtree(cache)
        result.update(status='SOURCE_AND_COMPLETE_RELEASE_VERIFIED_CACHE_CLEANED',raw_deleted=True,removed_raw_bytes=sum(x['bytes']for x in entries))
    except BaseException as e:result.update(status='DELIVERY_INCOMPLETE_NO_RETRY',error=repr(e),traceback=traceback.format_exc())
    dump(O/'DELIVERY_RESULT.json',result);dump(REC/'DELIVERY_RESULT.json',result)
    if result.get('remote_verified'):
        try:
            receipts=[REC/n for n in ['GIT_SYNC_RESULT.json','REMOTE_VERIFIED.json','DELIVERY_RESULT.json','CLEANUP_PLAN.json']if(REC/n).exists()]
            gh(['release','upload',TAG,*map(str,receipts),'--repo',REPO],30)
            cache=O/'receipt_restore';cache.mkdir(exist_ok=False)
            for p in receipts:
                gh(['release','download',TAG,'--repo',REPO,'--pattern',p.name,'--dir',str(cache)],15);assert sha(cache/p.name)==sha(p)
            shutil.rmtree(cache);dump(REC/'RECEIPTS_REMOTE_VERIFIED.json',dict(passed=True,files=[dict(name=p.name,sha256=sha(p))for p in receipts],no_second_push=True))
        except BaseException as e:dump(REC/'RECEIPT_ERROR.json',dict(error=repr(e)))
    print(json.dumps(result),flush=True)
if __name__=='__main__':
    if sys.argv[1:]==['prepare']:prepare()
    elif sys.argv[1:]==['deliver']:deliver()
    else:raise SystemExit('prepare or deliver')
