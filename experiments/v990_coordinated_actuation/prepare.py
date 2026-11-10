"""Freeze source-only qualification; explicitly no physical entry/window."""
import ast
import fcntl
import hashlib
import json
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
O=R/'runs/v990_coordinated_actuation';REC=R/'records/nav2_v990_20261110'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')


def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=sha(R/'REVIEW_PENDING');assert guard=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    red=read(O/'BASELINE_RED.json');control=read(O/'CONTROL_QUALIFICATION.json');binding=read(O/'BINDING_QUALIFICATION.json')
    assert red['original_failure_reproduced']and control['passed']and binding['passed']
    assert all(not(O/n).exists()for n in ['USER_APPROVAL.json','ROUND_WINDOW.json','AUTHORIZATION.json'])
    from authority import authorized
    try:authorized()
    except PermissionError:pass
    else:raise AssertionError('UNEXPECTED_MODEL_AUTHORITY')
    old=read(R/'experiments/v987_bounded_startup_components/SOURCE_FREEZE.json')['files'];files={}
    for name,h in old.items():assert sha(R/name)==h,name;files[name]=h
    REC.mkdir(exist_ok=True)
    for n in ['BASELINE_RED.json','CONTROL_QUALIFICATION.json','BINDING_QUALIFICATION.json','RESTORE_RECEIPT.json']:
        (REC/n).write_bytes((O/n).read_bytes());files[str((REC/n).relative_to(R))]=sha(REC/n)
    for p in C.iterdir():
        assert not p.is_symlink()
        if p.is_file()and p.name!='SOURCE_FREEZE.json':
            if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
            files[str(p.relative_to(R))]=sha(p)
    prior=R/'experiments/v987_bounded_startup_components/SOURCE_FREEZE.json';files[str(prior.relative_to(R))]=sha(prior)
    frozen=dict(final=True,source_only=True,models_before_freeze=0,integrations_before_freeze=0,models_authorized=False,
        scientific_source=str((C/'vehicle_control.py').relative_to(R)),old_v987_files_unchanged=len(old),files=files)
    p=C/'SOURCE_FREEZE.json'
    if p.exists():assert read(p)==frozen,'FROZEN_SOURCE_CHANGED'
    else:dump(p,frozen)
    final=dict(passed=True,status='SOURCE_AND_CONTROL_MAP_QUALIFIED_ONLY',models=0,actual_native=0,private_native=0,replay_native=0,
        physical_tracking_qualified=False,physical_ready=False,models_authorized=False,no_model_window_opened=True,
        actual_physical_engine_bound_to_candidate=False,real_installed_RPP_rerun_in_this_stage=False,
        control_checks=len(control['checks']),binding_checks=len(binding['checks']),binding_negatives=len(binding['negative_cases']),
        real_saved_input_map_calls=sum(x['saved_response_rows']for x in control['saved_cases']),
        fixed_boundary_cases=control['fixed_boundary_cases'],continuous_calls=control['continuous_sequence_inputs'],
        maximum_independent_rear_residual_rad_s=control['maximum_independent_rear_compatibility_residual_rad_s'],
        frozen_files=len(files),old_v987_files_unchanged=len(old),source_freeze_sha256=sha(p),review_pending_sha256=guard,
        original_v987_status='NOT_PASSED',report='docs/RPCCR_COORDINATED_ACTUATION_V990_REPORT.md')
    dump(REC/'FINAL_ZERO_MODEL_AUDIT.json',final)
    dump(REC/'AUTHORIZATION.json',dict(user_instruction='下一步我要看到好消息',scope='Implement coordinated actuator allocation and qualify without models',
        models_authorized=False,new_window_not_authorized=True,old_batches_not_reopened=True))
    state=read(R/'CURRENT_EXPERIMENT.json')
    state.update(status='REVIEW_PENDING',source_revision='V990_SOURCE_AND_CONTROL_MAP_QUALIFIED_ONLY',active_run=None,active_window=None,
        active_entrypoint=None,next_physical_authorized=False,execution_window_closed=True,v990_coordinated_actuation=final)
    dump(R/'CURRENT_EXPERIMENT.json',state)
    with(R/'RESEARCH_STATUS.md').open('a')as f:
        f.write('\n- V990协调控制分配源码/零模型资格完成：同一虚拟曲率联合前轮Ackermann角与后轮公共速度/差速，先求原幅值/速率与.6虚拟角速可行域，不逐轮事后裁剪；原1.5偏航反馈改作用于共同曲率，原PI8/4保留但公共速度可协调降低，停车保持共同曲率直到两后轮零。原V982/V987/第二保存态共904保存输入新映射、1080边界/连续20000调用和21角度完整目标停车全过，独立后轮一致性残差8.88e-16；原实际四帧红例保持失败。真实构造/CommandMap/切换/350软件派发记录与混合控制重建5.55e-17，10记录篡改负例拒绝。均非新物理响应；源1819旧文件保持，物理engine尚未接入候选/未重跑RPP软件动作、physical_ready=false，不自动模型或新90分钟/整路24。模型积分预测重放训练实机0，REVIEW_PENDING/锁保持。见docs/RPCCR_COORDINATED_ACTUATION_V990_REPORT.md。\n')
    print(json.dumps(final))


if __name__=='__main__':main()
