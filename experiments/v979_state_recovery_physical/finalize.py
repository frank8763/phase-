"""Bounded closed-batch accounting, report and verified evidence delivery; zero models."""
import ast,fcntl,hashlib,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v979_state_recovery_physical';REC=R/'records/nav2_v979_20261110'
TAG='phase-rpccr-state-recovery-v979-20261110';REPO='frank8763/phase-';GH=R/'tools/phase_storage_20261107/vendor/gh'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def run(args,timeout=30):
    x=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=timeout);assert x.returncode==0,(x.stderr or x.stdout)[-1800:];return x.stdout
def gh(args):return run([str(GH),*args,'--repo',REPO])
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert read(O/'COMPLETION.json')['closed']and read(O/'AUTHORIZATION.json')['models_authorized']is False
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    REC.mkdir(exist_ok=True)
    with(REC/'FINALIZE_CLAIM.json').open('x')as stream:json.dump(dict(at=time.time(),models=0),stream)
    completion=read(O/'COMPLETION.json');tasks=read(C/'TASKS.json');counts=[]
    for task in tasks:
        out=Path(task['output']);attempted=out.exists()
        n=read(out/'RESULT.json')if(out/'RESULT.json').exists()else{}
        checked=read(out/'INDEPENDENT_AUDIT.json')if(out/'INDEPENDENT_AUDIT.json').exists()else{}
        failure=n.get('prefix_failure')
        counts.append(dict(task_id=task['task_id'],stage=task['stage'],attempted=attempted,passed=checked.get('passed')is True,
                           historical_restore_native=(failure.get('historical_restore_native')if failure else n.get('historical_prefix_replay_native'))if attempted else 0,
                           new_branch_native=(failure.get('new_branch_native')if failure else n.get('new_branch_native'))if attempted else 0,
                           own_full_trace_replay_native=n.get('replay_native')if attempted else 0,
                           private_native=0,unexecuted=not attempted,error=checked.get('error',n.get('error')),
                           minimum_actual_clearance_m=checked.get('minimum_actual_clearance_m',checked.get('minimum_clearance_m')),
                           goal_m=n.get('goal_distance_m'),tracking=checked.get('tracking')))
    for rel,digest in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/rel)==digest,rel
    final=dict(closed=True,passed=completion['status']=='TWO_COMPONENTS_AND_ONE_WE_MAIN_REPEAT_PASSED'and all(x['passed']for x in counts),
               status=completion['status'],completion=completion,integrations=counts,source_sha_all_verified=True,
               new24_executed=0,independent_navigation_tasks=sum(x['attempted']for x in counts if x['stage']!='component'and x['task_id']!='repeat_we'),
               models_during_finalization=0,old_failure_preserved=True,review_pending_original_restored=True)
    dump(REC/'FINAL_INDEPENDENT_AUDIT.json',final)
    for name in ['AUTHORIZATION.before_close.json','ROUND_WINDOW.json','COMPLETION.json','RESULTS.json','REPEAT_CHECK.json','ZERO_MODEL_ENTRY_QUALIFICATION.json','RESTORE_RECEIPT.json']:
        if(O/name).exists():(REC/name).write_bytes((O/name).read_bytes())
    report=R/'docs/RPCCR_STATE_RECOVERY_PHYSICAL_V979_REPORT.md'
    lines=['# V979：冻结V977的有界物理验证','',f"结果：**{completion['status']}**。原V974失败及旧窗口保持，不是三路线/新24验收。",'',
           '顺序为两个原保存状态恢复组件，全通过才原西向东主与条件完整重复。任一功能/安全/证据异常即停；唯一90分钟模型截止不延长。',
           '历史前缀通过原body commands真实积分恢复，并逐原生比对完整状态/控制；与新分支、完整自身控制重放分账。未知不填0。','',
           '| 任务 | 尝试 | 通过 | 历史恢复积分 | 新分支积分 | 完整轨迹重放 |','|---|---:|---:|---:|---:|---:|']
    for row in counts:lines.append(f"| {row['task_id']} | {row['attempted']} | {row['passed']} | {row['historical_restore_native']} | {row['new_branch_native']} | {row['own_full_trace_replay_native']} |")
    lines+=['',f"停止原因：`{completion.get('error')}`",'',
             '全部训练/SAC/实体机0，Stage隔离；current/runtime/冻结网络不改。组件的ARM起点明确为原全局native/time，不冒称全局t0；没有车身根或时钟改写。完整动态链只由整路实际发现、实际续行>=1m、目标<=.45与停稳/全来源独立审核判定。',
             '重复沿原Nav2合同：同规范物理模型/初态与配置、两个完整链均过、各自全状态控制重放<=1e-8；异步完整轨迹可能不同，不能声称逐轨迹确定性。',
             '新保存态入口准备期同步构造阻塞观测、恢复历史缺初始发布时钟两项零模型错误保留，均在物理前修复；V977科学源字节不变。',
             '闭批恢复REVIEW_PENDING、模型授权关闭；没有自动三路线/24/通宵/新候选。必要证据远端SHA回读前保留，单次push/5秒远端核验失败不重试。']
    report.write_text('\n'.join(lines)+'\n')
    with(R/'RESEARCH_STATUS.md').open('a')as stream:stream.write('\n- FINAL V979：'+completion['status']+'；两保存组件/条件WE主重复准确或未知积分分账见docs/RPCCR_STATE_RECOVERY_PHYSICAL_V979_REPORT.md。首次失败依赖任务停止/旧失败截止保持，guard恢复/模型授权关闭；新24与训练实机0，无自动扩展。\n')
    # Exclude only the active finalizer console and campaign console from this
    # archive; the closed immutable report, evidence and errors remain complete.
    transport=R/'experiments/v978_source_only_closure/deliver.py';spec=importlib.util.spec_from_file_location('v979_source_only_archive_tools',transport);t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
    cloud=O/'cloud';cloud.mkdir(exist_ok=False);pack=t.packer(cloud)
    raw_roots=[O,R/'runs/v858_nav2_verified/v979']
    files=[]
    for root in raw_roots:
        for path in pack['walk'](root):
            if cloud in path.parents or path.parent==O and path.name in {'finalize.console','campaign.console'}:continue
            files.append(path)
    files+=list(pack['walk'](REC))+list(pack['walk'](C))+[report,R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md']
    assert sum(p.stat().st_size for p in files)<2*1024**3,'CACHE_BUDGET_EXCEEDED'
    group=pack['archive']('v979-fixed-recovery-physical-gate',files)
    index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',status=completion['status'],new24=0,
               archives=[{k:v for k,v in group.items()if k!='files'}]);dump(REC/'RECORD_INDEX.json',index)
    stage=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',str(report.relative_to(R)),str(C.relative_to(R)),str(REC.relative_to(R))]
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    run(['git','add','--',*stage]);run(['git','diff','--cached','--check'])
    for name in run(['git','diff','--cached','--name-only']).splitlines():assert(R/name).lstat().st_size<90*1024**2
    run(['git','commit','-m','Record frozen state-recovery physical gate and exact integration accounting'])
    commit=run(['git','rev-parse','HEAD']).strip();sync=dict(commit=commit,one_attempt=True,push_limit_s=30,remote_read_limit_s=5)
    with(REC/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as e:sync['push_error']=repr(e)
    try:sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==commit
    except Exception as e:sync['verify_error']=repr(e)
    dump(REC/'GIT_SYNC_RESULT.json',sync);assert sync.get('remote_head_verified'),'REMOTE_SOURCE_UNKNOWN_KEEP_RAW_NO_RETRY'
    gh(['release','create',TAG,'--target',commit,'--title','V977 fixed-state physical gate, no24 confirmation','--notes',completion['status']+'; original saved-state restoration and new branch/replay counters separately preserved; first failure stops.','--draft'])
    assets=[p for p in cloud.iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json'];gh(['release','upload',TAG,*map(str,assets)])
    readback=O/'readback';readback.mkdir(exist_ok=False)
    for path in assets:gh(['release','download',TAG,'--pattern',path.name,'--dir',str(readback)]);assert sha(path)==sha(readback/path.name)
    t.verifier()(readback,index);gh(['release','edit',TAG,'--draft=false'])
    receipts=O/'receipt_readback';receipts.mkdir(exist_ok=False)
    def receipt(path):
        gh(['release','upload',TAG,str(path)]);gh(['release','download',TAG,'--pattern',path.name,'--dir',str(receipts)]);assert sha(path)==sha(receipts/path.name)
    dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,source_commit=commit,all_source_and_member_sha_verified=True,models=0));receipt(REC/'REMOTE_VERIFIED.json');receipt(REC/'GIT_SYNC_RESULT.json')
    # Only closed physical outputs are cleaned here. Keep active operation logs
    # and tiny handoff/claims; no recursive deletion of the active finalizer.
    catalog={x['path']:x for x in group['files']}
    physical_root=R/'runs/v858_nav2_verified/v979';removed=0
    if physical_root.exists():
        for p in pack['walk'](physical_root):assert sha(p)==catalog[str(p.relative_to(R))]['sha256'];removed+=p.stat().st_size
        assert not physical_root.is_symlink();shutil.rmtree(physical_root)
    for folder in [O/'prior_v974',cloud,readback]:
        if folder.exists():
            assert folder.resolve().is_relative_to(R/'runs')and not folder.is_symlink()
            removed+=sum(p.stat().st_size for p in pack['walk'](folder));shutil.rmtree(folder)
    dump(REC/'CLEANUP_RESULT.json',dict(deleted_bytes=removed,remote_verified_before_cleanup=True,models=0));receipt(REC/'CLEANUP_RESULT.json')
    dump(REC/'FINALIZED.json',dict(closed=True,status=completion['status'],remote_verified=True,all_source_and_member_sha_verified=True,models=0,
         release_url=index['release_url'],models_authorized=False));receipt(REC/'FINALIZED.json');shutil.rmtree(receipts)
    run(['git','add','--',str(REC.relative_to(R))]);run(['git','commit','-m','Record V979 verified raw delivery receipts without a second push'])
    print(json.dumps(dict(finalized=True,status=completion['status'],deleted_bytes=removed,models=0)),flush=True)
if __name__=='__main__':main()
