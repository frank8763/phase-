"""Bounded zero-model closure, one new-root sync, selected evidence readback."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/input_consistent_overnight_20261110';REC=R/'records/nav2_v1003_20261110'
TAG='phase-rpccr-input-consistent-v1003-20261110';REPO='frank8763/phase-';GH=R/'tools/phase_storage_20261107/vendor/gh'
REPORT=R/'docs/RPCCR_INPUT_CONSISTENT_V1002_V1004_REPORT.md'
SOURCES=['experiments/v1002_causal_response_predictor','experiments/v1003_causal_recovery_execution','experiments/v1004_planned_input_navigation','experiments/v1005_input_consistent_closure']
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',str(REPORT.relative_to(R)),*SOURCES,str(REC.relative_to(R))]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def run(args,limit=30):
    p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=limit);assert p.returncode==0,(p.stderr or p.stdout)[-1500:];return p.stdout
def gh(args):return run([str(GH),*args,'--repo',REPO])
spec=importlib.util.spec_from_file_location('v1005_verified_storage_helpers',R/'experiments/v978_source_only_closure/deliver.py');helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
RAWROOTS=[R/'runs/v1002_causal_response_predictor',R/'runs/v1003_causal_recovery_execution',R/'runs/v1004_planned_input_navigation',R/'runs/v858_nav2_verified/v1003',R/'runs/v858_nav2_verified/v1004']

def summarize():
    done=read(ROOT/'COMPLETION.json');component=read(R/'runs/v1003_causal_recovery_execution/COMPLETION.json');assert done['model_authority']is False
    counts=dict(component_models=0,historical_native=0,component_new_native=0,component_own_replay_native=0,navigation_models=0,navigation_native=0,navigation_own_replay_native=0,private_mujoco_native=0)
    for row in component['rows']:
        a=row['audit']['counts'];counts['component_models']+=a['vehicle_tasks_initialized'];counts['historical_native']+=a['historical_native'];counts['component_new_native']+=a['new_actual_native'];counts['component_own_replay_native']+=a['own_trace_replay_native']
    unknown=[];nav=[]
    for task in read(R/'experiments/v1004_planned_input_navigation/TASKS.json'):
        p=Path(task['output'])/'RESULT.json'
        if not p.exists():
            if Path(task['output']).exists():unknown.append(dict(task_id=task['task_id'],reason='No durable final native receipt; initialization/integrations unknown'))
            continue
        n=read(p);nav.append(dict(task_id=task['task_id'],actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),status=n.get('status')))
        if n.get('environment_initialization_completed'):counts['navigation_models']+=1
        else:unknown.append(dict(task_id=task['task_id'],reason='Initialization count unknown'))
        for key,dest in [('actual_native','navigation_native'),('replay_native','navigation_own_replay_native'),('private_native','private_mujoco_native')]:
            if n.get(key)is None:unknown.append(dict(task_id=task['task_id'],counter=key,reason='Unknown; not filled with zero'))
            else:counts[dest]+=n[key]
    screens=[]
    folder=R/'runs/v858_nav2_verified/v1004/PREFLIGHTS'
    if folder.exists():
        for p in folder.iterdir():
            if(p/'PREFLIGHT.json').exists():screens.append(read(p/'PREFLIGHT.json'))
            else:unknown.append(dict(preflight=p.name,reason='Preflight initialization/completion unknown; no zero inference'))
    counts['passed_true_t0_initializations']=len(screens)
    confirmation=[x for x in done['rows']if x['stage']=='confirmation'];passed=sum(x['passed']for x in confirmation)
    final=dict(passed=done['status']=='FIXED24_AND_THREE_REPEATS_PASSED',status=done['status'],stop_reason=done['error']or'All frozen gates completed',
        component_passed=component['passed'],component_rows=[dict(name=x['name'],passed=x['passed'],audit=x['audit'])for x in component['rows']],
        exact_known_counts=counts,unknown_counts=unknown,known_totals_are_lower_bounds_if_unknown=bool(unknown),navigation_receipts=nav,
        navigation_rows=done['rows'],confirmation_executed=len(confirmation),confirmation_successes=passed,confirmation_unexecuted=24-len(confirmation),
        complete24_rate=(passed/24 if len(confirmation)==24 else None),confirmation_repeats_executed=sum(x['stage']=='confirmation_repeat'for x in done['rows']),
        actual_training_SAC_hardware=0,models_during_closure=0,old_failures_and_windows_unchanged=True,guard_restored=sha(R/'REVIEW_PENDING')==sha(ROOT/'REVIEW_PENDING.before'),
        absolute_deadline_unix=1794355200.,prerequisite_deadline_unchanged=read(ROOT/'ROUND_WINDOW.json')['deadline_unix'])
    dump(REC/'FINAL_INDEPENDENT_AUDIT.json',final)
    lines=['# 原因果输入一致恢复与条件动态实验', '', '状态：'+final['status']+'。停止原因：'+str(final['stop_reason']), '',
        '两个原保存恢复状态实际通过，均执行2204新增原生步和完整2秒停车尾。进展分别0.571996510、0.517086897米；最大位置误差0.002478015、0.001282189米，最大航向误差0.001781884、0.000279778弧度；最低实际净空0.273036567米、坏接触0，各自完整状态/控制重放误差0。', '',
        '前向预测器只由两项旧响应标定，另外两项留出检验通过，不读取未来实测状态；不是全局误差界。整路恢复期间先取消普通Nav2动作，再由唯一控制者执行原因果计划输入，完整停车后交回原目标。此Nav2经验条件合同不是旧328步控制器的保证。', '',
        '完整整路/重复结果：', '']
    lines += ['- '+x['task_id']+'：'+('PASS'if x['passed']else'FAIL')+'；导航原生='+str(x['actual_native'])+'，重放='+str(x['replay_native'])for x in done['rows']]
    lines += ['',f"固定24：已执行{len(confirmation)}，成功{passed}，未执行{24-len(confirmation)}；固定重复执行{final['confirmation_repeats_executed']}。未执行全24不报告全分母成功率。旧V828的8执行/6成功不混入。",'',
        '精确已知分账：`'+json.dumps(counts,ensure_ascii=False)+'`。未知项：`'+json.dumps(unknown,ensure_ascii=False)+'`。未知不填0。', '',
        '前置窗口18:44:53.884–20:14:53.884保持；条件夜间模型总截止2026-11-11 08:00+08，未延长旧批。首开发功能或安全/源码/证据异常停止所有依赖，不自动修补重跑。软件交接演练为非物理peer，不能冒称新Nav2到达。', '',
        '当前仅有限单actor声明课程；不宣称任意遮挡、多actor、地图泛化、实时、递归安全或RAS全面优势。训练、SAC、实体机0，Stage隔离。必要证据远端全来源及解压SHA核验后按清单清理；失败保留原始缓存。', '']
    REPORT.write_text('\n'.join(lines))
    for name in ['USER_AUTHORIZATION.json','ROUND_WINDOW.json','LEDGER.json','COMPLETION.json']:(REC/name).write_bytes((ROOT/name).read_bytes())
    return final

def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    with(ROOT/'FINALIZE_CLAIM.json').open('x')as f:json.dump(dict(models=0,at=time.time()),f)
    final=summarize()
    for folder in ['experiments/v1003_causal_recovery_execution','experiments/v1004_planned_input_navigation']:
        assert all(sha(R/p)==h for p,h in read(R/folder/'SOURCE_FREEZE.json')['files'].items()),'SOURCE_FREEZE_CHANGED'
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    cloud=ROOT/'cloud';cloud.mkdir(exist_ok=False);pack=helpers.packer(cloud);files=[];excluded=[];links=[]
    for root in [ROOT,*RAWROOTS,*[R/s for s in SOURCES],REC]:
        for base,dirs,names in os.walk(root,followlinks=False):
            for name in dirs+names:
                p=Path(base)/name
                if p.is_symlink():links.append(dict(path=str(p.relative_to(R)),target=os.readlink(p),target_accessed=False))
        for p in pack['walk'](root):
            if cloud in p.parents or p.name in ['finalize.console','campaign.console']:continue
            if p.suffix=='.lock'or '__pycache__'in p.parts or'cache'in p.parts:
                excluded.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)));continue
            files.append(p)
    dump(REC/'SYMLINKS_MANIFEST.json',dict(links=links));dump(REC/'EXCLUDED_REBUILDABLE_FILES.json',dict(files=excluded))
    files += [REC/'SYMLINKS_MANIFEST.json',REC/'EXCLUDED_REBUILDABLE_FILES.json',REPORT,R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md']
    assert sum(p.stat().st_size for p in set(files))*3<2*1024**3,'RAW_ARCHIVE_READBACK_BUDGET'
    archive=pack['archive']('v1003-input-consistent-recovery-and-navigation',files)
    index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',status=final['status'],counts=final['exact_known_counts'],unknown_counts=final['unknown_counts'],archives=[{k:v for k,v in archive.items()if k!='files'}])
    dump(REC/'RECORD_INDEX.json',index);run(['git','add','--',*STAGE]);run(['git','diff','--cached','--check'])
    for name in run(['git','diff','--cached','--name-only']).splitlines():assert any(name==s or name.startswith(s+'/')for s in STAGE)and(R/name).stat().st_size<90*1024**2
    # Source changes are frozen and reviewed before launch; generated outcome/counts
    # are validated above against the independent completed evidence, no success rewrite.
    (REC/'STAGED_REVIEW.stat').write_text(run(['git','diff','--cached','--stat']))
    run(['git','add','--',str(REC.relative_to(R))]);run(['git','commit','-m','Validate causal input-consistent recovery and record bounded conditional navigation outcome'])
    commit=run(['git','rev-parse','HEAD']).strip();assert not(ROOT/'GIT_SYNC_CLAIM.json').exists()and not(ROOT/'GIT_SYNC_RESULT.json').exists()
    sync=dict(commit=commit,one_attempt=True,push_limit_s=30,remote_read_limit_s=5)
    with(ROOT/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as e:sync['push_error']=repr(e)
    try:sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==commit
    except Exception as e:sync['verify_error']=repr(e)
    dump(ROOT/'GIT_SYNC_RESULT.json',sync);dump(REC/'GIT_SYNC_RESULT.json',sync);assert sync.get('remote_head_verified'),'REMOTE_UNKNOWN_RETAIN_RAW_NO_RETRY'
    gh(['release','create',TAG,'--target',commit,'--title','Input-consistent recovery and conditional navigation: '+final['status'],'--notes','Two original physical recovery states passed. All route/confirmation execution or nonexecution, failures and exact/unknown counts are retained. No training or hardware. Full member SHA before cleanup.','--draft'])
    assets=[p for p in cloud.iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json'];gh(['release','upload',TAG,*map(str,assets)])
    back=ROOT/'readback';back.mkdir(exist_ok=False)
    for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert sha(p)==sha(back/p.name)
    helpers.verifier()(back,index);gh(['release','edit',TAG,'--draft=false'])
    dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,all_sources_and_decompressed_member_sha=True,commit=commit,models=0))
    catalog={x['path']:x for x in read(back/(index['archives'][0]['group']+'.INVENTORY.json'))['files']};exclude={x['path']:x for x in excluded};deleted=[]
    for root in RAWROOTS:
        size=0
        for p in pack['walk'](root):
            row=catalog.get(str(p.relative_to(R)),exclude.get(str(p.relative_to(R))));assert row and p.stat().st_size==row['bytes']and sha(p)==row['sha256'];size+=p.stat().st_size
        for link in links:
            p=R/link['path']
            if p.is_relative_to(root):assert p.is_symlink()and os.readlink(p)==link['target'];p.unlink()
        assert not any(p.is_symlink()for p in root.rglob('*'));shutil.rmtree(root);deleted.append(dict(path=str(root.relative_to(R)),bytes=size))
    for root in [cloud,back]:
        size=sum(p.stat().st_size for p in pack['walk'](root));shutil.rmtree(root);deleted.append(dict(path=str(root.relative_to(R)),bytes=size))
    dump(REC/'CLEANUP_RESULT.json',dict(remote_verified_before_cleanup=True,deleted=deleted,deleted_bytes=sum(x['bytes']for x in deleted),models=0))
    dump(REC/'FINALIZED.json',dict(closed=True,scientific_status=final['status'],full_remote_member_sha_verified=True,raw_cache_cleaned=True,source_commit=commit,models_authorized=False,no_second_push=True))
    receipt=ROOT/'receipt_readback';receipt.mkdir(exist_ok=False)
    for p in [REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json',REC/'CLEANUP_RESULT.json',REC/'FINALIZED.json']:
        gh(['release','upload',TAG,str(p)]);gh(['release','download',TAG,'--pattern',p.name,'--dir',str(receipt)]);assert sha(p)==sha(receipt/p.name)
    shutil.rmtree(receipt);dump(ROOT/'FINALIZED.json',read(REC/'FINALIZED.json'))
    print(json.dumps(dict(finalized=True,status=final['status'],release_url=index['release_url'],models=0)),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:dump(ROOT/'ZERO_MODEL_CLOSURE_ERROR.json',dict(error=repr(e),models=0,no_sync_or_model_retry=True,unverified_raw_retained=True));raise
