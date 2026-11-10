"""Zero-model entry-continuation evidence; Release increment, never another push."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/input_consistent_entry_20261110';O=R/'runs/v1006_navigation_entry_continuation';REC=R/'records/nav2_v1006_20261110'
TAG='phase-rpccr-input-consistent-v1003-20261110';REPO='frank8763/phase-';GH=R/'tools/phase_storage_20261107/vendor/gh'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gh(args):
    p=subprocess.run([str(GH),*args,'--repo',REPO],cwd=R,capture_output=True,text=True,timeout=30);assert p.returncode==0,(p.stderr or p.stdout)[-1000:];return p.stdout
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert read(ROOT/'COMPLETION.json')['models_authorized']is False
    with(ROOT/'ZERO_MODEL_CLOSURE_CLAIM.json').open('x')as f:json.dump(dict(models=0,at=time.time()),f)
    REC.mkdir(exist_ok=False);done=read(ROOT/'COMPLETION.json');tasks=read(C/'TASKS.json');counts=dict(initialized_known=0,navigation_known=0,replay_known=0,private_known=0);unknown=[]
    for task in tasks:
        out=Path(task['output']);p=out/'RESULT.json'
        if not p.exists():
            if out.exists():unknown.append(dict(task_id=task['task_id'],reason='Missing final native accounting; do not infer0'))
            continue
        n=read(p)
        if n.get('environment_initialization_completed'):counts['initialized_known']+=1
        else:unknown.append(dict(task_id=task['task_id'],counter='initialized'))
        for src,dest in [('actual_native','navigation_known'),('replay_native','replay_known'),('private_native','private_known')]:
            if n.get(src)is None:unknown.append(dict(task_id=task['task_id'],counter=src))
            else:counts[dest]+=n[src]
    mains=[x for x in done['rows']if x['stage']=='confirmation'];summary=dict(status=done['status'],error=done['error'],known_counts=counts,unknown_counts=unknown,
        complete24_rate=sum(x['passed']for x in mains)/24 if len(mains)==24 else None,confirmation_executed=len(mains),confirmation_unexecuted=24-len(mains),
        old_v1004_prearm_abort_preserved=True,original_precondition_deadline_unchanged=1794312893.8843997,absolute_deadline_unix=1794355200.,models_during_closure=0,no_second_push=True)
    dump(REC/'FINAL_INDEPENDENT_AUDIT.json',summary)
    report=R/'docs/RPCCR_ENTRY_CONTINUATION_V1006_REPORT.md'
    report.write_text('# V1006原点元数据入口接续\n\n状态：'+done['status']+'；停止原因：'+str(done['error'])+'。\n\n仅显式补齐原点0元数据，原V1004全部科学源码复用不改，三个原t0复用未重跑。原V1004模型已加载/ARM前KeyError/导航0及次级缺REPLAY错误永久保留，不追认通过。两原恢复组件的通过仍独立保存。原20:14:53.884前置截止与次日08:00总截止均未延长。\n\n当前新接续已知分账：`'+json.dumps(counts)+'`；未知项：`'+json.dumps(unknown)+'`，有未知时已知和为下界，未知不填0。\n\n确认已执行'+str(len(mains))+'，未执行'+str(24-len(mains))+'；未完成24不报全分母率。无训练/SAC/实机/Stage。非实时、泛化或RAS保证。\n')
    for name in ['APPROVAL.json','ORIGINAL_WINDOW.json','COMPLETION.json','LEDGER.json']:(REC/name).write_bytes((ROOT/name).read_bytes())
    s=importlib.util.spec_from_file_location('v1006_verified_archive_helpers',R/'experiments/v978_source_only_closure/deliver.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
    cloud=ROOT/'cloud';cloud.mkdir(exist_ok=False);pack=h.packer(cloud);rawroots=[O,R/'runs/v858_nav2_verified/v1006'];files=[];excluded=[]
    for root in [ROOT,*rawroots,C,REC]:
        for p in pack['walk'](root):
            if cloud in p.parents:continue
            if p in [ROOT/'finalize.console',ROOT/'campaign.console']:continue
            if p.suffix=='.lock'or'__pycache__'in p.parts or'cache'in p.parts:
                excluded.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)));continue
            files.append(p)
    files.append(report);assert sum(p.stat().st_size for p in set(files))*3<2*1024**3
    archive=pack['archive']('v1006-single-entry-continuation',files);index=dict(repository=REPO,release_tag=TAG,source_commit='643aa3e10cd8d90860a5ce1223251b3d06abfc16',source_increment_in_release=True,summary=summary,archives=[{k:v for k,v in archive.items()if k!='files'}])
    dump(REC/'V1006_RECORD_INDEX.json',index);assets=[p for p in cloud.iterdir()if p.is_file()]+[REC/'V1006_RECORD_INDEX.json'];gh(['release','upload',TAG,*map(str,assets)])
    back=ROOT/'readback';back.mkdir(exist_ok=False)
    for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert sha(p)==sha(back/p.name)
    h.verifier()(back,index);catalog={x['path']:x for x in read(back/(index['archives'][0]['group']+'.INVENTORY.json'))['files']};ex={x['path']:x for x in excluded};deleted=[]
    for root in rawroots:
        if not root.exists():continue
        rows=list(pack['walk'](root));size=0
        for p in rows:
            rel=str(p.relative_to(R));row=catalog.get(rel,ex.get(rel));assert row and p.stat().st_size==row['bytes']and sha(p)==row['sha256'];size+=p.stat().st_size
        # Engine resource links are unlinked, never followed outside this root.
        for base,dirs,names in os.walk(root,followlinks=False):
            for name in dirs+names:
                p=Path(base)/name
                if p.is_symlink():p.unlink()
        shutil.rmtree(root);deleted.append(dict(path=str(root.relative_to(R)),bytes=size))
    for root in [cloud,back]:shutil.rmtree(root)
    final=dict(closed=True,status=done['status'],archive_member_sha_remote_verified=True,raw_cache_cleaned=True,models_authorized=False,no_second_push=True,deleted=deleted)
    dump(REC/'V1006_FINALIZED.json',final);dump(ROOT/'FINALIZED.json',final)
    gh(['release','upload',TAG,str(REC/'V1006_FINALIZED.json')]);print(json.dumps(final),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:dump(ROOT/'ZERO_MODEL_CLOSURE_ERROR.json',dict(error=repr(e),models=0,raw_retained=True,no_model_or_push_retry=True));raise
