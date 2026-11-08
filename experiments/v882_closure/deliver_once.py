"""One bounded V882-only Git/Release delivery; no model imports or old batch retries."""
import fcntl,gzip,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,tarfile,time,traceback
R=pathlib.Path(__file__).resolve().parents[2];O=R/'runs/v882_runtime_evidence_repair';REC=R/'records/nav2_v882_20261108';CLOUD=O/'cloud';GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';TAG='phase-nav2-v882-20261108'
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def read(p):return json.loads(p.read_text())
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
def main():
    assert read(O/'COMPLETION.json')['closed']and read(O/'FINALIZED.json')['source_and_decompressed_sha_verified']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    with(O/'DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),pid=os.getpid(),one_new_v882_attempt=True,models=0),f)
    result=dict(status='LOCAL_CLOSED_REMOTE_PENDING',models=0,integrations=0,raw_deleted=False,old_batch_sync_retried=False)
    try:
        # Distinct closed-log/supplement archive; never rewrite the main archive.
        spec=importlib.util.spec_from_file_location('v882_ops_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=CLOUD
        files=[]
        for base in [R/'experiments/v881_timing_accounting_continuation',R/'experiments/v882_closure',REC]:files.extend(m.walk(base))
        files += [O/n for n in ['finalize.console','validation.console','FINALIZED.json','HANDOFF.md','PRODUCTION_BINDINGS.json']]
        files += [R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'docs/NAV2_RUNTIME_V882_REPORT.md',R/'docs/NAV2_RUNTIME_V882_PREPARATION.md']
        supplement=m.archive('v882-closed-operations',[p for p in files if p.is_file()and '__pycache__'not in p.parts])
        index=read(CLOUD/'RECORD_INDEX.json');index['archives'].append({k:v for k,v in supplement.items()if k!='files'});dump(CLOUD/'RECORD_INDEX.json',index);dump(REC/'RECORD_INDEX.json',index)
        names=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/NAV2_RUNTIME_V882_REPORT.md','docs/NAV2_RUNTIME_V882_PREPARATION.md','experiments/v881_timing_accounting_continuation','experiments/v882_runtime_evidence_repair','experiments/v882_closure','records/nav2_v882_20261108']
        for args in [['git','add','--',*names],['git','diff','--cached','--check']]:
            p=command(args);assert p.returncode==0,p.stderr+p.stdout
        staged=command(['git','diff','--cached','--name-only']).stdout.splitlines()
        for name in staged:assert name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md']or any(name.startswith(n+'/')or name==n for n in names[2:]);assert (R/name).stat().st_size<90*1024**2
        (O/'SOURCE_REVIEW.console').write_text(command(['git','diff','--cached','--stat']).stdout)
        p=command(['git','commit','-m','Repair bounded runtime evidence and record failed NS navigation validation']);assert p.returncode==0,p.stderr
        head=command(['git','rev-parse','HEAD']).stdout.strip();result['source_commit']=head
        sync=dict(source_commit=head,attempted_once=True,push_budget_s=30,read_budget_s=5,push_succeeded=False,remote_head_verified=False)
        with(O/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
        try:
            p=command(['git','push','origin','main'],30);sync.update(push_succeeded=p.returncode==0,returncode=p.returncode);(O/'push.console').write_text(p.stdout+p.stderr)
        except subprocess.TimeoutExpired:sync['push_error']='30S_TIMEOUT_NO_RETRY'
        try:
            p=command(['git','ls-remote','origin','refs/heads/main'],5);remote=p.stdout.split()[0]if p.returncode==0 and p.stdout.strip()else None;sync.update(remote_head=remote,remote_head_verified=remote==head)
        except subprocess.TimeoutExpired:sync['read_error']='5S_TIMEOUT_NO_RETRY'
        dump(REC/'GIT_SYNC_RESULT.json',sync);dump(O/'GIT_SYNC_RESULT.json',sync)
        if not sync['remote_head_verified']:raise RuntimeError('SOURCE_REMOTE_NOT_VERIFIED_PRESERVE_RAW_NO_RETRY')
        print('SOURCE_REMOTE_VERIFIED '+head,flush=True)
        release=json.loads(gh(['api',f'repos/{REPO}/releases','--method','POST','-f','tag_name='+TAG,'-f','target_commitish='+head,'-F','draft=true','-f','name=V882 bounded runtime and failed static NS','-f','body=One static NS attempt failed;17981 actual and own replay,zero state error,minimum clearance0.256874m,goal remaining2.312238m. Runtime100ms gate passed;ROS cache watchdog and local controller collision block remain. No dynamic or24 confirmation. Full necessary records and digests included.'],30))
        dump(O/'RELEASE_CREATED.json',dict(id=release['id'],tag_name=TAG));items=[CLOUD/'RECORD_INDEX.json']
        for g in index['archives']:items += [CLOUD/(g['group']+'.INVENTORY.json'),*[CLOUD/p['name']for p in g['parts']]]
        gh(['release','upload',TAG,*map(str,items),'--repo',REPO],60)
        print('RELEASE_ASSETS_UPLOADED',flush=True)
        assets=json.loads(gh(['api',f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100'],15));by_name={a['name']:a for a in assets};verified=[]
        for p in items:
            a=by_name[p.name];assert a['size']==p.stat().st_size and a.get('digest')=='sha256:'+sha(p)
        cache=O/'remote_restore';cache.mkdir(exist_ok=False)
        gh(['release','download',TAG,'--repo',REPO,'--dir',str(cache)],60)
        for p in items:assert sha(cache/p.name)==sha(p);verified.append(dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size))
        # Restore each remotely downloaded member to disk independently, then hash.
        restored=0
        for g in index['archives']:
            inventory=read(cache/(g['group']+'.INVENTORY.json'));expected={x['path']:x for x in inventory['files']};archive=cache/'joined.tar.zst'
            with archive.open('xb')as f:
                for part in g['parts']:
                    with(cache/part['name']).open('rb')as source:shutil.copyfileobj(source,f)
            assert sha(archive)==g['archive_sha256'];proc=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE);seen=set()
            try:
                with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
                    for member in tf:
                        name=pathlib.Path(member.name);assert not name.is_absolute()and '..'not in name.parts and member.name not in seen;row=expected[member.name];assert member.isfile()and row['type']=='file'and member.size==row['bytes'];seen.add(member.name)
                        target=cache/'one_member'
                        with target.open('xb')as f:shutil.copyfileobj(tf.extractfile(member),f)
                        assert sha(target)==row['sha256'];target.unlink();restored+=1
                assert proc.wait(timeout=20)==0 and seen==set(expected)
            finally:
                if proc.poll()is None:proc.kill();proc.wait()
            archive.unlink()
        gh(['release','edit',TAG,'--repo',REPO,'--draft=false'],30)
        proof=dict(passed=True,assets=verified,actual_members_restored=restored,remote_source_verified=True,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',at=time.time());dump(REC/'REMOTE_VERIFIED.json',proof)
        # Only this closed V882 raw/cache, no SDK or previous evidence deletion.
        candidates=[R/'runs/v858_nav2_verified/v882',CLOUD,cache];entries=[]
        for p in candidates:
            assert p.resolve().is_relative_to(R/'runs')and not p.is_symlink()
            entries += [dict(path=str(q.relative_to(R)),bytes=q.lstat().st_size)for q in p.rglob('*')if q.is_file()and not q.is_symlink()]
        (REC/'CLEANUP_FILES.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x)for x in entries)+'\n').encode(),mtime=0))
        for p in candidates:shutil.rmtree(p)
        result.update(status='SOURCE_RELEASE_DOWNLOAD_AND_MEMBER_RESTORE_VERIFIED_CLOSED_V882_RAW_CLEANED',raw_deleted=True,remote_verified=True,release_url=proof['release_url'],removed_bytes=sum(x['bytes']for x in entries))
    except BaseException as e:result.update(status='DELIVERY_INCOMPLETE_PRESERVE_REQUIRED_RAW_NO_RETRY',error=repr(e),traceback=traceback.format_exc())
    dump(REC/'DELIVERY_RESULT.json',result);dump(O/'DELIVERY_RESULT.json',result)
    # Receipts may be committed locally; never a second push.
    command(['git','add','records/nav2_v882_20261108']);p=command(['git','commit','-m','Record V882 one-shot delivery receipt without another push']);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
