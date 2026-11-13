"""Close failed daytime evidence with versioned, inactive operational logs."""
import sys,json,hashlib,fcntl,shutil,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1092_stopped_replan';D=R/'records/nav2_v1092_20261113'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def main():
    assert not(D/'FINALIZED_REVIEW.json').exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    summary=json.loads((O/'COMPLETION.json').read_text());review=json.loads((O/'FAILED_REVIEW.json').read_text());timed=json.loads((O/'TIMED_HYPOTHESIS.json').read_text());spatial=json.loads((O/'SPATIAL_HYPOTHESIS.json').read_text())
    assert summary['closed']and not summary['passed']and review['evidence_integrity_passed']
    text='''

日间独立回核：6个完整实际恢复段，39660新实际/39660自身重放，误差0，坏接触0，最低实际净空0.276984656m；终态平速0.000004714m/s，实际发现停车后净位移1.528498m，原目标余2.364657m。25门仅原目标到达失败，其余24门通过。不是跟踪失控、控制权抢占或未实际停车，不能报整路通过。

下一原因验证均0模型：原静态目标路的16个等待相位全在动态净空门拒绝，故单纯错峰不能解决这条路径。把真实测距原因果全周期占据外盒仅加入拓扑提案后，固定20k仅得到安全局部源，未得到完整原目标源；不能声称新路线已就绪。物理场景19实体/单actor、原安全门均未改。下一步需要动态占据感知的完整拓扑搜索/可执行转弯衔接，而非延长导航时间或继续复跑同路。

冻结前两次软件失败（240s完整等待相位搜索、固定旧观测名义拼接拒绝）及只读预编译准备错误保持；闭批诊断还发现原扩展审核把局部finite_plan误当模块属性，已仅在0模型诊断命名空间绑定原函数后完成回核；冻结物理/审核源未改。空间提案首个外盒坐标编码错误被原独立证书拒绝，已保存0模型失败并按原中心/半长接口更正，未用于物理。

当前已恢复REVIEW_PENDING原字节、执行锁空闲，不自动新物理、EW/NS、24或通宵。原NS主/重复成功和所有旧失败保留。初始归档内活跃closure日志是当时快照；此闭批补充归档保存完成后的日志及完整诊断快照，不覆盖原归档。
'''
    report=R/'docs/RPCCR_STOPPED_REPLAN_V1092_REPORT.md'
    report.write_text(report.read_text()+text)
    current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,automatic_additional_simulation=False,next_scope='Prepare dynamically informed complete topology from saved39660 root; no new model authorized by closure',latest_report=str(report.relative_to(R)),latest_failure_review={'evidence_integrity_passed':True,'functional_passed':False,'failed_gates':['goal'],'remaining_goal_m':2.3646573630322374})
    dump(R/'CURRENT_EXPERIMENT.json',current)
    with (R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1092闭批独立24/25门PASS，唯一原目标到达false；39660新实际/39660完整重放误差0，6实际完整段，末余2.364657m/平速4.714e-6/最低.276985/坏接触0。16等待相位全动态净空拒绝；原因果动态外盒拓扑20k仍仅安全局部源，0新模型，非下一版整路资格。冻结源不改，原扩展审核命名空间缺陷仅诊断修复；完整操作失败保留。当前REVIEW_PENDING/锁空闲，无追加物理或24。\n')
    logs=O/'closed_logs';logs.mkdir()
    for name in ['driver.console','closure.console']:shutil.copyfile(O/name,logs/name)
    spec=importlib.util.spec_from_file_location('review_snapshot_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
    files=list(arc.walk(C))+list(arc.walk(logs))+[p for p in O.iterdir()if p.is_file()]+[report,R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'runs/v858_nav2_verified/v1092/main_west_east/FAILED_ROUTE_INDEPENDENT_AUDIT.json']
    record,inventory=arc.package(R,files,O/'review_cloud','v1092-closed-review')
    dump(D/'REVIEW_INVENTORY.json',dict(files=inventory));index=json.loads((D/'RECORD_INDEX.json').read_text());index['archives'].append(record);index['archive_inventories']=['INVENTORY.json','REVIEW_INVENTORY.json'];index['source_snapshots_versioned']=True;dump(D/'RECORD_INDEX.json',index)
    dump(D/'FINALIZED_REVIEW.json',dict(evidence_integrity_passed=True,functional_passed=False,all_archived_source_and_decompressed_sha_verified=True,parts_reassembled_sha_verified=True,guard_original=True,phase_lock_idle=True,models=0,integrations=0))
    print(json.dumps(dict(review_archived=True,source_members=len(inventory),bytes=record['archive_bytes'],functional_passed=False,models=0)),flush=True)
if __name__=='__main__':main()
