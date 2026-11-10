"""Close a source-only candidate; never grant physical execution authority."""
import ast,fcntl,hashlib,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v984_decoupled_yaw_servo';REC=R/'records/nav2_v984_20261110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=sha(R/'REVIEW_PENDING');assert guard=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    old=json.loads((R/'experiments/v982_precise_recovery_gate/SOURCE_FREEZE.json').read_text())
    assert all(sha(R/p)==h for p,h in old['files'].items())
    assert json.loads((R/'runs/v982_precise_recovery_gate/COMPLETION.json').read_text())['closed']
    for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    red=json.loads((O/'BASELINE_RED.json').read_text());qual=json.loads((O/'CONTROL_MAP_QUALIFICATION.json').read_text())
    diag=json.loads((O/'ACTUATION_DIAGNOSIS.json').read_text());ind=json.loads((O/'INDEPENDENT_CONTROL_AUDIT.json').read_text())
    assert red['exact_original_map_reconstructed']and red['original_driving_map_ignores_measured_yaw']and red['passed']is False
    assert qual['passed']and ind['passed']and not qual['closed_loop_tracking_qualified']
    assert not diag['hypothesis_results']['unique_physical_root_cause_proven']
    assert not any((O/n).exists()for n in ['ROUND_WINDOW.json','USER_APPROVAL.json','AUTHORIZATION.json'])
    REC.mkdir(exist_ok=True)
    for name in ['BASELINE_RED.json','CONTROL_MAP_QUALIFICATION.json','ACTUATION_DIAGNOSIS.json','INDEPENDENT_CONTROL_AUDIT.json']:
        (REC/name).write_bytes((O/name).read_bytes())
    dump(REC/'AUTHORIZATION.json',dict(user_instruction='继续',scope='source and zero-model diagnosis/repair only',models_authorized=False,
         physical_ready=False,previous_v982='CLOSED_NOT_PASSED',no_window_extension=True))
    files={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()and p.name!='SOURCE_FREEZE.json'}
    for p in [R/'experiments/v958_hold_steering_contract/vehicle_control.py',R/'experiments/v949_steering_handoff/vehicle_control.py',
              R/'experiments/v856_nav2_foundation/vehicle_control.py',R/'runtime/mk-mini/training/assets/mkmini_real/mkmini_mobile_manipulator_indoor_v1.xml']:
        files[str(p.relative_to(R))]=sha(p)
    frozen=dict(final=True,models_before_freeze=0,integrations_before_freeze=0,model_authority=False,
        previous_physical_manifest='experiments/v982_precise_recovery_gate/SOURCE_FREEZE.json',
        previous_physical_manifest_sha256=sha(R/'experiments/v982_precise_recovery_gate/SOURCE_FREEZE.json'),files=files)
    target=C/'SOURCE_FREEZE.json'
    if target.exists():assert json.loads(target.read_text())==frozen,'ALREADY_FROZEN_SOURCE_CHANGED'
    else:dump(target,frozen)
    final=dict(passed=True,status='SOURCE_AND_CONTROL_MAP_QUALIFIED_ONLY',models=0,actual_native=0,private_native=0,replay_native=0,
        new_navigation_samples=0,new24=0,training=0,hardware=0,models_authorized=False,physical_ready=False,
        old_v982_status='NOT_PASSED',old_frozen_files_verified=len(old['files']),
        original_control_rows_reconstructed=6415,control_map_checks=len(qual['checks']),boundary_cases=qual['boundary_cases'],
        independent_witnesses=ind['independent_saved_witnesses'],negative_cases=len(ind['negative_cases']),
        source_freeze_sha256=sha(target),review_pending_sha256=guard,execution_lock_idle=True,
        remaining='Bind a separately authorized physical batch at exact original restored origins; measure actual drive and complete brake response before any full route.',
        exact_physical_bug_regression_status='NOT_YET_TESTED; saved old physical heading trace still fails .035rad',
        report='docs/RPCCR_DECOUPLED_YAW_V984_REPORT.md')
    dump(REC/'FINAL_ZERO_MODEL_AUDIT.json',final)
    state=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());state.update(status='REVIEW_PENDING',source_revision='V984_SOURCE_AND_CONTROL_MAP_ONLY',
        active_entrypoint=None,active_run=None,active_window=None,next_physical_authorized=False,execution_window_closed=True,
        decision_freeze='experiments/v984_decoupled_yaw_servo/SOURCE_FREEZE.json',protocol='experiments/v984_decoupled_yaw_servo/PROTOCOL.md',
        report=final['report'],v984_source_repair=final)
    dump(R/'CURRENT_EXPERIMENT.json',state)
    line='\n- V984仅保存数据诊断/控制映射修订：V958原6415控制重建误差1.11e-16，实测偏航变化不改变原后轮目标；固定94原生车体偏航与实测后轮差速残差RMS .010193rad/s，小于前轮运动学.047357，后轴参考点换算反而增加横向残差。不唯一归因摩擦/滑移/伺服负载，既有后轮速度伺服仍在。新候选仅后轮差速加1.5实测偏航反馈、.16等效目标帽和原幅值/速率/同公共速度/原轮目标符号投影；前轮及同记忆原刹停保持。14映射检查/240边界/11独立见证/7篡改负例通过；旧观测上的反事实指令不是新轨迹，真实航向修复/稳定性未证。V982 NOT_PASSED及1637旧冻结文件保持，本轮模型/积分/私有/重放/导航/训练实机0、无新窗，guard/锁保持；下一仍需两原保存状态闭环与完整尾资格，不自动整路24。见docs/RPCCR_DECOUPLED_YAW_V984_REPORT.md。\n'
    status=R/'RESEARCH_STATUS.md'
    if 'V984仅保存数据诊断/控制映射修订'not in status.read_text():
        with status.open('a')as f:f.write(line)
    print(json.dumps(final))
if __name__=='__main__':main()
