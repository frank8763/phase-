"""Saved-only closure; preserve raw data if bounded remote verification fails."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/explicit_checker_20261110';O=R/'runs/v1009_explicit_checker_navigation';REC=R/'records/nav2_v1009_20261110'
TAG='phase-rpccr-valid-path-v1009-20261110';REPO='frank8763/phase-';GH=R/'tools/phase_storage_20261107/vendor/gh'
REPORT=R/'docs/RPCCR_VALID_PATH_NAVIGATION_V1009_REPORT.md'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args,cap=30):
    p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=cap)
    assert p.returncode==0,(p.stderr or p.stdout)[-1500:];return p.stdout
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert read(ROOT/'COMPLETION.json')['models_authorized']is False and read(ROOT/'APPROVAL.json')['models_authorized']is False
    with(ROOT/'ZERO_MODEL_CLOSURE_CLAIM.json').open('x')as f:json.dump(dict(models=0,at=time.time()),f)
    REC.mkdir(exist_ok=True);done=read(ROOT/'COMPLETION.json');tasks=read(C/'TASKS.json')
    counts=dict(navigation_models_known=0,navigation_native_known=0,own_replay_native_known=0,private_native_known=0,preflight_models_known=0);unknown=[];started=[]
    for task in tasks:
        out=Path(task['output']);p=out/'RESULT.json'
        if not p.exists():
            if out.exists():unknown.append(dict(task_id=task['task_id'],reason='No final native accounting; unknown is not zero'))
        else:
            started.append(task['task_id']);n=read(p)
            if n.get('environment_initialization_completed'):counts['navigation_models_known']+=1
            else:unknown.append(dict(task_id=task['task_id'],counter='model_initialization'))
            for src,dest in [('actual_native','navigation_native_known'),('replay_native','own_replay_native_known'),('private_native','private_native_known')]:
                if n.get(src)is None:unknown.append(dict(task_id=task['task_id'],counter=src))
                else:counts[dest]+=n[src]
    unique={t['preflight_output']for t in tasks}
    for name in unique:
        p=Path(name)/'PREFLIGHT.json'
        if p.exists():counts['preflight_models_known']+=read(p)['models_initialized']
        elif Path(name).exists():unknown.append(dict(preflight=name,counter='initialization_without_final_receipt'))
    mains=[x for x in done['rows']if x['stage']=='confirmation'];repeats=[x for x in done['rows']if x['stage']=='confirmation_repeat']
    summary=dict(status=done['status'],error=done['error'],known_counts=counts,unknown_counts=unknown,started_navigation_tasks=started,
        confirmation_executed=len(mains),confirmation_unexecuted=24-len(mains),confirmation_successes=sum(x['passed']for x in mains),
        full24_rate=sum(x['passed']for x in mains)/24 if len(mains)==24 else None,confirmation_repeats=repeats,
        old_V1004_V1006_failures_preserved=True,V1003_components_reused_not_repeated=True,models_during_closure=0,
        current_guard_original=True,execution_lock_idle=True,absolute_deadline_unix=1794355200.)
    dump(REC/'FINAL_INDEPENDENT_AUDIT.json',summary)
    REPORT.write_text('# V1009普通Nav2检查器与有效路径保持\n\n状态：'+done['status']+'。停止原因：`'+str(done['error'])+'`。\n\n只改普通BT的明确目标检查器与官方有效当前路径保持；其余物理/恢复控制/传感/安全门不改。V1010完整安装软件动作成功仅是非物理资格；V1003两个实际恢复组件通过保持，V1004与V1006原失败不抹去。\n\n实际分账（未知不填0）：\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\n旧批次、组件、开发、重复均不混新24分母。未完成全24不报全分母率。无训练、实机或Stage；不宣称实时、任意地图/遮挡、多actor、递归安全或RAS优势。\n')
    for name in ['APPROVAL.json','ROUND_WINDOW.json','COMPLETION.json','LEDGER.json']:(REC/name).write_bytes((ROOT/name).read_bytes())
    spec=importlib.util.spec_from_file_location('v1009_saved_archive',R/'experiments/v978_source_only_closure/deliver.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    cloud=ROOT/'cloud';cloud.mkdir(exist_ok=False);pack=h.packer(cloud);rawroots=[O,R/'runs/v858_nav2_verified/v1009'];files=[];links=[]
    for root in [ROOT,*rawroots,C,REC]:
        if not root.exists():continue
        for base,dirs,names in os.walk(root,followlinks=False):
            for name in dirs+names:
                p=Path(base)/name
                if p.is_symlink():links.append(dict(path=str(p.relative_to(R)),target=os.readlink(p)))
        for p in pack['walk'](root):
            if cloud in p.parents or p in [ROOT/'finalize.console',ROOT/'campaign.console']or'__pycache__'in p.parts:continue
            files.append(p)
    dump(REC/'RESOURCE_LINK_METADATA.json',links);files.extend([REC/'RESOURCE_LINK_METADATA.json',REPORT])
    assert sum(p.stat().st_size for p in set(files))*3<2*1024**3,'ARCHIVE_TEMPORARY_BUDGET_EXHAUSTED_RAW_RETAINED'
    archive=pack['archive']('v1009-full-route-evidence',files)
    index=dict(repository=REPO,release_tag=TAG,summary=summary,archives=[{k:v for k,v in archive.items()if k!='files'}]);dump(REC/'RECORD_INDEX.json',index)
    net_end=time.monotonic()+180.
    def gh(args):return run([str(GH),*args,'--repo',REPO],cap=max(.1,min(30.,net_end-time.monotonic())))
    gh(['release','create',TAG,'--target','main','--title','V1009 valid-path navigation evidence','--notes','Bounded frozen candidate; status and exact accounting in RECORD_INDEX.json.'])
    assets=[p for p in cloud.iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json'];gh(['release','upload',TAG,*map(str,assets)])
    back=ROOT/'readback';back.mkdir(exist_ok=False);gh(['release','download',TAG,'--dir',str(back)])
    for p in assets:assert sha(p)==sha(back/p.name),'REMOTE_ASSET_SHA_MISMATCH'
    h.verifier()(back,index);dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,all_parts_and_decompressed_member_sha=True,at=time.time()))
    catalog={x['path']:x for x in read(back/(index['archives'][0]['group']+'.INVENTORY.json'))['files']};deleted=[]
    for root in rawroots:
        if not root.exists():continue
        size=0
        for p in pack['walk'](root):
            if'__pycache__'in p.parts:continue
            row=catalog[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'];size+=p.stat().st_size
        for base,dirs,names in os.walk(root,followlinks=False):
            for name in dirs+names:
                p=Path(base)/name
                if p.is_symlink():assert any(x['path']==str(p.relative_to(R))and x['target']==os.readlink(p)for x in links);p.unlink()
        shutil.rmtree(root);deleted.append(dict(path=str(root.relative_to(R)),bytes=size))
    for root in [cloud,back]:shutil.rmtree(root)
    final=dict(closed=True,models_authorized=False,status=done['status'],all_remote_source_member_SHA_verified=True,raw_cleanup=deleted)
    dump(REC/'FINALIZED.json',final);dump(ROOT/'FINALIZED.json',final)
    # Review and commit only this candidate's known paths; unrelated work stays untouched.
    paths=[str(C.relative_to(R)),str(REC.relative_to(R)),str(REPORT.relative_to(R)),'CURRENT_EXPERIMENT.json']
    run(['git','add','--',*paths]);review=run(['git','diff','--cached','--stat','--',*paths]);dump(ROOT/'STAGED_REVIEW.json',dict(known_paths=paths,stat=review,models=0))
    run(['git','commit','--only','-m','Record bounded V1009 valid-path navigation outcome','--',*paths])
    claim=ROOT/'GIT_SYNC_CLAIM.json'
    with claim.open('x')as f:json.dump(dict(at=time.time(),push_cap_s=30,head_cap_s=5),f)
    sync=dict(push_attempted=True,remote_verified=False,head=run(['git','rev-parse','HEAD']).strip())
    try:
        run(['git','push','origin','HEAD:main'],30);remote=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_verified']=remote==sync['head'];sync['remote_head']=remote
    except BaseException as e:sync['error']=repr(e)
    dump(ROOT/'GIT_SYNC_RESULT.json',sync);dump(REC/'GIT_SYNC_RESULT.json',sync)
    gh(['release','upload',TAG,str(REC/'FINALIZED.json'),str(REC/'GIT_SYNC_RESULT.json')]);print(json.dumps(final),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:dump(ROOT/'ZERO_MODEL_CLOSURE_ERROR.json',dict(error=repr(e),models=0,raw_retained=True,no_automatic_retry=True));raise
