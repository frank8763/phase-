"""Idempotence-protected zero-model accounting and local archive closure."""
import fcntl,importlib.util,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v909_timed_command_contract';REC=R/'records/nav2_v909_20261109'
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import verify_sources
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not(O/'FINALIZED.json').exists(),'ALREADY_FINALIZED'
    done=json.loads((O/'COMPLETION.json').read_text());assert done['closed'];verify_sources(R,C/'SOURCE_FREEZE.json')
    assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    REC.mkdir(exist_ok=True)
    for name in ['COMPLETION.json','RESULTS.json','AUTHORIZATION.json','ROUND_WINDOW.json','ZERO_MODEL_QUALIFICATION.json','RELEASE_QUALIFICATION.json','PREPARATION_ERRORS.json','PLATFORM_RESULT.json','REPEAT.json']:
        if(O/name).exists():(REC/name).write_bytes((O/name).read_bytes())
    platform=json.loads((O/'PLATFORM_RESULT.json').read_text())if(O/'PLATFORM_RESULT.json').exists()else{}
    total=lambda key:None if any(x.get(key)is None for x in done['rows'])else sum(x[key]for x in done['rows'])
    summary=dict(status=done['status'],platform_actual_native=platform.get('actual_native'),platform_own_replay_native=platform.get('replay_native'),
                 navigation_actual_native=total('actual_native'),navigation_own_replay_native=total('replay_native'),navigation_private_native=total('private_native'),
                 platform_passed=platform.get('passed',False),attempted_navigation=len(done['rows']),unexecuted_navigation=done['unexecuted_navigation'],new24=0,training=0,hardware=0,
                 deadline_unix=done['deadline_unix'],remote_pending=True,closed_reason=done['error'])
    (REC/'RESULT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    report=R/'docs/NAV2_TIMED_COMMAND_V909_REPORT.md'
    report.write_text('# V909 有限命令与刹停时序管道\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\n本轮仅固定18工况执行/刹停资格及条件原西向东主任务和重复。旧失败和旧截止保持。内部六秒驻留门被显式修改，新的误差界只属经验资格和在线监测，不是递归安全证明、24项验收或RAS创新证明。所有原生净空、接触、控制和完整重放门保持。未执行的导航不计失败率分母。\n')
    spec=importlib.util.spec_from_file_location('v909_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=False)
    files=[]
    for base in [C,R/'runs/v858_nav2_verified/v909',REC]:files.extend(m.walk(base))
    files.extend(p for p in m.walk(O)if not any(x in p.relative_to(O).parts for x in ['cloud','restore','saved']) and p.name not in ['campaign.console','finalize.console'])
    files.append(report);archive=m.archive('phase-v909-20261109',files)
    (REC/'RECORD_INDEX.json').write_text(json.dumps(dict(repository='frank8763/phase-',release_tag='phase-timed-command-v909-20261109',archives=[{k:v for k,v in archive.items()if k!='files'}]),indent=2)+'\n')
    proof=dict(status='LOCAL_FINALIZED_REMOTE_PENDING',scientific_status=done['status'],all_sources_and_decompressed_sha_verified=True,models=0,integrations=0,at=time.time())
    (REC/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');(O/'FINALIZED.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
