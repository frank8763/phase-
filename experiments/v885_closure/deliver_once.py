"""Zero-model V885 delivery; one source push, verified Release restore before cleanup."""
import fcntl,gzip,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,tarfile,time,traceback
R=pathlib.Path(__file__).resolve().parents[2]
O=R/'runs/v885_remaining_static_routes'; REC=R/'records/nav2_v885_20261108'; CLOUD=O/'cloud'
GH=R/'tools/phase_storage_20261107/vendor/gh'; REPO='frank8763/phase-'; TAG='phase-nav2-v885-20261108'
NAMES=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/NAV2_RUNTIME_V885_REPORT.md','experiments/v885_remaining_static_routes','experiments/v885_closure','records/nav2_v885_20261108']
def dump(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
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
def closed_lock():
    assert read(O/'COMPLETION.json')['closed'] and read(O/'FINALIZED.json')['source_and_decompressed_sha_verified']
    assert read(O/'COMBINED_THREE_ROUTE_GATE.json')['combined_three_route_static_development_passed']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    return lock
def prepare():
    lock=closed_lock()
    assert not (O/'DELIVERY_CLAIM.json').exists()
    spec=importlib.util.spec_from_file_location('v885_ops_archive',R/'experiments/v856_nav2_closure/package_records.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=CLOUD
    files=[]
    for base in [R/'experiments/v885_closure',REC,R/'runs/v884_feasible_rpp/install']:
        files.extend(m.walk(base))
    files += [O/n for n in ['finalize.console','validation.console','FINALIZED.json','HANDOFF.md','combined_gate.console','COMBINED_THREE_ROUTE_GATE.json','summarize.console','USER_ADVANCE.json','ROUND_WINDOW.json']]
    files += [R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'docs/NAV2_RUNTIME_V885_REPORT.md']
    supplement=m.archive('v885-closed-operations',[p for p in files if p.is_file()and '__pycache__'not in p.parts])
    index=read(CLOUD/'RECORD_INDEX.json')
    assert [x['group']for x in index['archives']]==['v885-runtime-evidence']
    index['archives'].append({k:v for k,v in supplement.items()if k!='files'})
    index['release_url']=f'https://github.com/{REPO}/releases/tag/{TAG}'
    index['shared_runtime_reference']='records/nav2_v856_20261107/RECORD_INDEX.json; V884 scientific sources are in Git, required V884 plugin install included in closed operations'
    dump(CLOUD/'RECORD_INDEX.json',index);dump(REC/'RECORD_INDEX.json',index)
    print('PREPARED_NO_MODEL_NO_NETWORK',flush=True)
def main():
    lock=closed_lock()
    for n in ['DELIVERY_CLAIM.json','GIT_SYNC_CLAIM.json','GIT_SYNC_RESULT.json','RELEASE_CREATED.json','DELIVERY_RESULT.json']:
        assert not (O/n).exists(),n+' already exists; do not repeat delivery'
    with(O/'DELIVERY_CLAIM.json').open('x')as f:
        json.dump(dict(at=time.time(),pid=os.getpid(),one_new_v885_attempt=True,models=0),f)
    result=dict(status='LOCAL_CLOSED_REMOTE_PENDING',models=0,integrations=0,raw_deleted=False,old_batch_sync_retried=False)
    try:
        index=read(CLOUD/'RECORD_INDEX.json')
        assert len(index['archives'])==2
        p=command(['git','diff','--cached','--check']);assert p.returncode==0,p.stdout+p.stderr
        staged=command(['git','diff','--cached','--name-only']).stdout.splitlines();assert staged
        for name in staged:
            assert any(name==n or name.startswith(n+'/')for n in NAMES),name
            assert (R/name).stat().st_size<90*1024**2,name
        (O/'SOURCE_REVIEW.console').write_text(command(['git','diff','--cached','--stat']).stdout)
        p=command(['git','commit','-m','Pass same-version three-route static regression with complete reruns']);assert p.returncode==0,p.stderr
        head=command(['git','rev-parse','HEAD']).stdout.strip();result['source_commit']=head
        sync=dict(source_commit=head,attempted_once=True,push_budget_s=30,read_budget_s=5,push_succeeded=False,remote_head_verified=False)
        with(O/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
        try:
            p=command(['git','push','origin','main'],30)
            sync.update(push_succeeded=p.returncode==0,returncode=p.returncode);(O/'push.console').write_text(p.stdout+p.stderr)
        except subprocess.TimeoutExpired:sync['push_error']='30S_TIMEOUT_NO_RETRY'
        try:
            p=command(['git','ls-remote','origin','refs/heads/main'],5)
            remote=p.stdout.split()[0]if p.returncode==0 and p.stdout.strip()else None
            sync.update(remote_head=remote,remote_head_verified=remote==head)
        except subprocess.TimeoutExpired:sync['read_error']='5S_TIMEOUT_NO_RETRY'
        dump(REC/'GIT_SYNC_RESULT.json',sync);dump(O/'GIT_SYNC_RESULT.json',sync)
        if not sync['remote_head_verified']:raise RuntimeError('SOURCE_REMOTE_NOT_VERIFIED_PRESERVE_RAW_NO_RETRY')
        print('SOURCE_REMOTE_VERIFIED '+head,flush=True)
        body='Same V884 scientific version: original NS main and complete repeat reused from verified V884, plus WE and EW main/complete reruns all passed. Four new navigations:36708 actual native and36708 exact own-control replay steps; including NS:54043/54043. Minimum actual clearance0.211161m,zero bad contacts,zero own-state replay error,strict goal arrival and stopped. Original safety/control/timing gates retained. Asynchronous reruns are not bitwise identical trajectories. Three fixed static development routes,not independent dynamic/new24 confirmation; no comparison,ablation,training or real robot. Source and every remotely downloaded archived member verified before local temporary evidence cleanup.'
        release=json.loads(gh(['api',f'repos/{REPO}/releases','--method','POST','-f','tag_name='+TAG,'-f','target_commitish='+head,'-F','draft=true','-f','name=V885 same-version three static routes and complete reruns passed','-f','body='+body]))
        dump(O/'RELEASE_CREATED.json',dict(id=release['id'],tag_name=TAG))
        items=[CLOUD/'RECORD_INDEX.json']
        for g in index['archives']:
            items += [CLOUD/(g['group']+'.INVENTORY.json'),*[CLOUD/p['name']for p in g['parts']]]
        gh(['release','upload',TAG,*map(str,items),'--repo',REPO],60)
        print('RELEASE_ASSETS_UPLOADED',flush=True)
        assets=json.loads(gh(['api',f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100'],15));by_name={a['name']:a for a in assets}
        for p in items:
            a=by_name[p.name];assert a['size']==p.stat().st_size and a.get('digest')=='sha256:'+sha(p),p.name
        cache=O/'remote_restore';cache.mkdir(exist_ok=False)
        gh(['release','download',TAG,'--repo',REPO,'--dir',str(cache)],60)
        verified=[]
        for p in items:
            assert sha(cache/p.name)==sha(p),p.name
            verified.append(dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size))
        restored=0;originals={}
        for g in index['archives']:
            inventory=read(cache/(g['group']+'.INVENTORY.json'));expected={x['path']:x for x in inventory['files']}
            originals.update(expected);archive=cache/'joined.tar.zst'
            with archive.open('xb')as f:
                for part in g['parts']:
                    with(cache/part['name']).open('rb')as source:shutil.copyfileobj(source,f)
            assert sha(archive)==g['archive_sha256']
            proc=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE);seen=set()
            try:
                with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
                    for member in tf:
                        name=pathlib.Path(member.name)
                        assert not name.is_absolute()and '..'not in name.parts and member.name not in seen
                        row=expected[member.name];assert member.isfile()and row['type']=='file'and member.size==row['bytes'];seen.add(member.name)
                        target=cache/'one_member'
                        with target.open('xb')as f:shutil.copyfileobj(tf.extractfile(member),f)
                        assert sha(target)==row['sha256'],member.name
                        target.unlink();restored+=1
                assert proc.wait(timeout=20)==0 and seen==set(expected)
            finally:
                if proc.poll()is None:proc.kill();proc.wait()
            archive.unlink()
        gh(['release','edit',TAG,'--repo',REPO,'--draft=false'])
        proof=dict(passed=True,assets=verified,actual_members_restored=restored,remote_source_verified=True,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',at=time.time())
        dump(REC/'REMOTE_VERIFIED.json',proof)
        raw=R/'runs/v858_nav2_verified/v885';candidates=[raw,CLOUD,cache];entries=[]
        for base in candidates:
            assert base.resolve().is_relative_to(R/'runs')and not base.is_symlink()
            for q in base.rglob('*'):
                assert not q.is_symlink(),str(q)
                if not q.is_file():continue
                rel=str(q.relative_to(R));digest=sha(q)
                if base==raw:assert rel in originals and digest==originals[rel]['sha256'],rel
                entries.append(dict(path=rel,bytes=q.stat().st_size,sha256=digest))
        (REC/'CLEANUP_FILES.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x)for x in entries)+'\n').encode(),mtime=0))
        for row in entries:assert sha(R/row['path'])==row['sha256'],row['path']
        for base in candidates:shutil.rmtree(base)
        result.update(status='SOURCE_RELEASE_DOWNLOAD_AND_MEMBER_RESTORE_VERIFIED_CLOSED_V885_RAW_CLEANED',raw_deleted=True,remote_verified=True,release_url=proof['release_url'],actual_members_restored=restored,removed_bytes=sum(x['bytes']for x in entries))
        print('ALL_REMOTE_MEMBERS_RESTORED '+str(restored),flush=True)
    except BaseException as e:
        result.update(status='DELIVERY_INCOMPLETE_NO_RETRY',error=repr(e),traceback=traceback.format_exc())
    dump(REC/'DELIVERY_RESULT.json',result);dump(O/'DELIVERY_RESULT.json',result)
    if result.get('remote_verified'):
        try:
            receipts=[REC/n for n in ['REMOTE_VERIFIED.json','DELIVERY_RESULT.json','CLEANUP_FILES.jsonl.gz','GIT_SYNC_RESULT.json']]
            gh(['release','upload',TAG,*map(str,receipts),'--repo',REPO],30)
            receipt_cache=O/'receipt_restore';receipt_cache.mkdir(exist_ok=False)
            for p in receipts:
                gh(['release','download',TAG,'--repo',REPO,'--pattern',p.name,'--dir',str(receipt_cache)],15)
                assert sha(receipt_cache/p.name)==sha(p),p.name
            shutil.rmtree(receipt_cache)
            dump(REC/'RECEIPTS_REMOTE_VERIFIED.json',dict(passed=True,files=[dict(name=p.name,sha256=sha(p))for p in receipts],at=time.time(),no_second_push=True))
            result['post_delivery_receipts_remote_verified']=True
        except BaseException as e:
            result['receipt_upload_error']=repr(e)
    dump(O/'DELIVERY_RESULT.json',result)
    print(json.dumps(result),flush=True)
if __name__=='__main__':
    if sys.argv[1:]==['prepare']:prepare()
    elif not sys.argv[1:]:main()
    else:raise SystemExit('use no arguments for one-shot delivery, or prepare')
