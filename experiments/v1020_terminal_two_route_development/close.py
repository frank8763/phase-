"""Offline-safe saved-only closure; remote failure retains bounded evidence."""
import fcntl,json,os,shutil,subprocess,time
from pathlib import Path
from archive import walk,sha,package,verify
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1020_terminal_two_route_development';ROOT=R/'runs/terminal_two_route_20261110';REC=R/'records/nav2_v1020_20261110'
TAG='phase-rpccr-exact-entry-night-v1020-20261110';GH=R/'tools/phase_storage_20261107/vendor/gh';REPORT=R/'docs/RPCCR_TERMINAL_TWO_ROUTE_V1020_REPORT.md'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def run(args,cap=30):
    p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=cap);assert p.returncode==0,(p.stdout+p.stderr)[-1200:];return p.stdout
def cache_size():return sum(p.stat().st_size for root in [ROOT,O,R/'runs/v858_nav2_verified/v1020',R/'runs/atomic_handoff_night_20261110',R/'runs/v1014_atomic_handoff_navigation',R/'runs/v858_nav2_verified/v1014']for p in walk(root))
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not read(ROOT/'APPROVAL.json')['models_authorized']and read(ROOT/'COMPLETION.json')['closed']
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    with(ROOT/'ZERO_MODEL_CLOSURE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    REC.mkdir(exist_ok=True);done=read(ROOT/'COMPLETION.json');tasks=read(C/'TASKS.json');counts=dict(navigation_models=0,navigation_native=0,own_replay_native=0,private_native=0,preflight_models=0,reused_original_preflight_models=0);unknown=[]
    for task in tasks:
        out=Path(task['output']);p=out/'RESULT.json'
        if not p.exists():
            if out.exists():unknown.append(dict(task=task['task_id'],counter='missing_final_native_receipt'))
            continue
        n=read(p)
        if n.get('environment_initialization_completed'):counts['navigation_models']+=1
        else:unknown.append(dict(task=task['task_id'],counter='initialization'))
        for source,dest in [('actual_native','navigation_native'),('replay_native','own_replay_native'),('private_native','private_native')]:
            if n.get(source)is None:unknown.append(dict(task=task['task_id'],counter=source))
            else:counts[dest]+=n[source]
    for out in {t['preflight_output']for t in tasks}:
        p=Path(out)/'PREFLIGHT.json'
        if p.exists():
            reused={t['preflight_output']for t in tasks if t['slot']<4}
            key='reused_original_preflight_models'if out in reused else'preflight_models'
            counts[key]+=read(p)['models_initialized']
        elif Path(out).exists():unknown.append(dict(preflight=out,counter='initialization_without_final_receipt'))
    mains=[x for x in done['rows']if x['stage']=='development_sweep16'];summary=dict(status=done['status'],stop_reason=done['error'],known_counts=counts,unknown_counts=unknown,
        route_branch_rows=done['rows'][:4],development16_executed=len(mains),development16_unexecuted=16-len(mains),development16_successes=sum(x['passed']for x in mains),complete_development16_descriptive_rate=sum(x['passed']for x in mains)/16 if len(mains)==16 else None,
        original_three_route24_acceptance_passed=False,original_EW_initial_zero_gate_unqualified=True,navigation_budget_s=300,old_180s_failures_not_upgraded=True,models_during_closure=0,old_failures_preserved=True,guard_original=True,execution_lock_idle=True)
    dump(REC/'V1020_FINAL_INDEPENDENT_AUDIT.json',summary)
    REPORT.write_text('# V1020完整输入预测准入的恢复搜索通宵实验\n\n状态：'+done['status']+'。截止2026-11-11 09:00，不延长；旧失败/窗口保持。\n\n科学：完整实际输入预测不合格时继续原5000扩展/12边/5秒搜索，直到同一原.4米进展/原完整几何和停车门通过；不只检验第一条简化路径。保留新鲜零速许可与恢复停车所有权原子交接；新300秒导航内最多8完整进展段，每段原输入/几何/跟踪/200步停车门不变；非终点仍.4米进展，终点段仅以预测终点距离+.08<=.45及实际终点<=.45替代进展门，提交前预留完整段时间。纯解析预测和转向元数据重建允许1e-12浮点差（1e-9篡改拒绝），实际qpos/qvel/ctrl/mocap全重放仍1e-8，控制与身体请求仍精确。\n\n分账：\n\n```json\n'+json.dumps(summary,indent=2,ensure_ascii=False)+'\n```\n\n这是两个合法起点路线的300秒开发及条件新16开发（10120001–16），不是原180秒、原三路线或固定24验收；旧10110001–24仍未执行。完整行驶发现、因果控制、实际停车、续行、目标和完整重放全部门通过才记成功。开发/重复/旧批不混新24；未执行不报0/24。有限单actor课程，非任意地图/遮挡/多actor/实时/递归安全或RAS保证。训练/实机/Stage0。网络离线时保留有界必要原证据，待重新联网进行零模型上传校验。\n')
    for name in ['APPROVAL.json','ROUND_WINDOW.json','COMPLETION.json','LEDGER.json']:(REC/name).write_bytes((ROOT/name).read_bytes())
    raw=[O,R/'runs/v858_nav2_verified/v1020'];links=[];files=[]
    for root in [*raw,C,REC,ROOT]:
        for base,dirs,names in os.walk(root,followlinks=False):
            for name in dirs+names:
                p=Path(base,name)
                if p.is_symlink():links.append(dict(path=str(p.relative_to(R)),target=os.readlink(p)))
        files.extend(p for p in walk(root)if p not in [ROOT/'campaign.console',ROOT/'finalize.console']and p.suffix!='.lock')
    dump(REC/'RESOURCE_LINKS.json',links);files.extend([REC/'RESOURCE_LINKS.json',REPORT,R/'CURRENT_EXPERIMENT.json'])
    record,catalog=package(R,files,ROOT/'cloud','v1020-entry-full-night-evidence',lambda:cache_size()<2*1024**3-64*1024**2)
    index=dict(repository='frank8763/phase-',release_tag=TAG,summary=summary,archives=[record]);ip=REC/'V1020_RECORD_INDEX.json';dump(ip,index)
    # Science is closed even when the Internet is absent. No model/push retries.
    local=dict(closed=True,status=done['status'],models_authorized=False,local_source_member_sha_verified=True,remote_verified=False,raw_retained=True)
    dump(ROOT/'CLOSED_LOCAL.json',local)
    net_end=time.monotonic()+300.
    def gh(args):return run([str(GH),*args,'--repo','frank8763/phase-'],max(.1,min(30.,net_end-time.monotonic())))
    try:
        gh(['release','view',TAG,'--json','id'])
        assets=list((ROOT/'cloud').iterdir())+[ip,REPORT,REC/'V1020_FINAL_INDEPENDENT_AUDIT.json'];gh(['release','upload',TAG,*map(str,assets)])
        back=ROOT/'readback';back.mkdir(exist_ok=False)
        for p in [ROOT/'cloud'/(record['group']+'.INVENTORY.json'),ip]:
            gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert sha(p)==sha(back/p.name)
        def provider(part):
            gh(['release','download',TAG,'--pattern',part['name'],'--dir',str(back)]);return back/part['name'],True
        verify(record,catalog,provider)
        mapping={x['path']:x for x in catalog};deleted=[]
        for folder in raw:
            size=0
            for p in walk(folder):
                if p.suffix=='.lock':
                    assert p.stat().st_size==0,'NONEMPTY_LOCK_NOT_ARCHIVED';continue
                row=mapping[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'];size+=p.stat().st_size
            for base,dirs,names in os.walk(folder,followlinks=False):
                for name in dirs+names:
                    p=Path(base,name)
                    if p.is_symlink():assert any(x['path']==str(p.relative_to(R))and x['target']==os.readlink(p)for x in links);p.unlink()
            if folder.exists():shutil.rmtree(folder);deleted.append(dict(path=str(folder.relative_to(R)),bytes=size))
        for folder in [ROOT/'cloud',back]:shutil.rmtree(folder)
        final=dict(local,remote_verified=True,raw_retained=False,all_remote_decompressed_member_sha_verified=True,deleted=deleted)
        dump(REC/'V1020_FINALIZED.json',final);dump(ROOT/'FINALIZED.json',final);gh(['release','upload',TAG,str(REC/'V1020_FINALIZED.json')])
    except BaseException as error:
        dump(ROOT/'REMOTE_PENDING.json',dict(local,error=repr(error),no_automatic_retry=True));dump(REC/'REMOTE_PENDING.json',dict(local,error=repr(error),no_automatic_retry=True))
    paths=[str(REC.relative_to(R)),str(REPORT.relative_to(R)),'CURRENT_EXPERIMENT.json']
    run(['git','add','--',*paths]);run(['git','diff','--cached','--check','--',*paths]);run(['git','commit','--only','-m','Record closed V1020 offline night outcome and verified accounting','--',*paths])
    print(json.dumps(summary),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as error:dump(ROOT/'ZERO_MODEL_CLOSURE_ERROR.json',dict(error=repr(error),models=0,raw_retained=True,no_model_restart=True));raise
