"""Zero-model preparation closure; no physics, no network, immutable claim."""
import ast,fcntl,json,shutil,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1061_three_route_readiness';D=R/'records/nav2_v1061_20261111';sys.path.insert(0,str(C))
from archive import sha,walk

def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 assert not(O/'FINALIZE_CLAIM.json').exists(),'NO_FINALIZER_RETRY';dump(O/'FINALIZE_CLAIM.json',dict(at=time.time(),models=0));lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=sha(R/'REVIEW_PENDING');assert guard=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert not json.loads((O/'APPROVAL.json').read_text())['models_authorized'];assert not(O/'ROUND_WINDOW.json').exists();assert not any((C/n).exists()for n in ['worker.py','driver.py','start.py'])
 qualifications=['READINESS.json','CONTRACT_QUALIFICATION.json','SCENE_BINDING_QUALIFICATION.json','NS_SOFTWARE_CONTRACT_QUALIFICATION.json','PUBLICATION_QUALIFICATION.json','INDEPENDENT_SOFTWARE_AUDIT.json','FIXED_CLOCK_PUBLICATION_AUDIT.json'];objects={n:json.loads((O/n).read_text())for n in qualifications};assert objects['READINESS.json']['preparation_checks_passed']and objects['READINESS.json']['route_admission_passed']and not objects['READINESS.json']['ready_for_physics'];assert all(x['passed']for n,x in objects.items()if n!='READINESS.json')
 files={}
 for version in ['v1058_fresh_repeat_entry','v1060_bounded_publication_capture']:
  for path,expected in json.loads((R/'experiments'/version/'SOURCE_FREEZE.json').read_text())['files'].items():
   if not path.startswith(('experiments/','runtime/','current/','tools/')):continue
   p=R/path;assert p.is_file()and sha(p)==expected,'PREVIOUS_FROZEN_SOURCE_CHANGED '+path;files[path]=expected
 for p in walk(C):
  if p.name=='SOURCE_FREEZE.json'or p.suffix=='.pyc':continue
  if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
  files[str(p.relative_to(R))]=sha(p)
 for p in [O/'APPROVAL.json',O/'AUTHORIZATION.json',O/'COURSE_AUTHORIZATION.json',O/'DEPENDENCY_BINDING.json']:files[str(p.relative_to(R))]=sha(p)
 freeze=dict(files=files,models=0,mujoco_integrations=0,physical_authority=False,course_id='V1061_EW_START_NORTH_010',old_windows_closed=True);dump(C/'SOURCE_FREEZE.json',freeze)
 for p,h in files.items():assert sha(R/p)==h
 D.mkdir(exist_ok=True)
 for n in qualifications+['COURSE_AUTHORIZATION.json','AUTHORIZATION.json','EAST_WEST_ORIGINAL_START_GATE.json','EAST_WEST_ACTIVE_T0_METADATA.json','DEPENDENCY_BINDING.json','FIXED_POINT_EQUIVALENCE_AUDIT.json','STATIC_SOURCE_QUALIFICATION.json']:shutil.copyfile(O/n,D/n)
 summary=dict(status='SOFTWARE_PREPARATION_PASSED_NO_PHYSICS',course_id=freeze['course_id'],original_EW_rejection_kept=True,selected_course_static_complete_sources=3,software_qualification_passed=True,models_authorized=False,physics_ready=False,counts=dict(model_initializations=0,new_navigation_native=0,historical_replay_native=0,own_replay_native=0,private_mujoco_native=0,training_updates=0),new_six_route_tasks='UNEXECUTED',new24='UNEXECUTED',guard_original=True,old_failures_and_windows_unchanged=True)
 dump(D/'FINAL_SUMMARY.json',summary);dump(O/'COMPLETION.json',dict(closed=True,**summary));dump(D/'FINAL_INDEPENDENT_AUDIT.json',dict(passed=True,source_files=len(files),all_frozen_source_sha_verified=True,qualifications=qualifications,guard_sha256=guard,execution_lock_idle=True,no_new_physical_window_or_entry=True,counts=summary['counts'],synthetic_NS_source_not_actual_dynamic_pass=True,original_EW_task_not_passed=True))
 current=R/'CURRENT_EXPERIMENT.json';state=json.loads(current.read_text());state.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True);state['v1061_three_route_software_preparation']=dict(**summary,report='docs/RPCCR_THREE_ROUTE_READINESS_V1061_REPORT.md',source_freeze='experiments/v1061_three_route_readiness/SOURCE_FREEZE.json');dump(current,state)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n\n- V1061用户明确登记新课程V1061_EW_START_NORTH_010，仅EW起点(4,-2)北移0.10m到(4,-1.9)，原EW统一预测储备不足拒绝保留；WE/NS及原种子相位/目标/19实体/actor/模型和安全门不变。新课程3完整静态源及共同软件资格通过，新EW28590解析原生最低raw.244661516/门.243534210/目标上界.420630944/重建误差0；实际arena数组起点绑定通过，非MJB或物理审核。修复generic终点/完整控制漏门，固定原800零输入hold后的唯一时钟完整重建；NS合成域长输入及微小非静止夹具约6秒<原8秒、全预测/ctrl/请求误差0，非真实NS动态源。经典WE全部数组不变，3×11软件发布/过期与时钟负例通过。严格用户源码资格限定，0模型/积分/导航/训练/实机、6新主重复与24未执行，没有新窗口或物理worker，不自动启动。原V1058重复38929实测过期失败及20:30截止保持。SOURCE_FREEZE/独立审核/报告见docs/RPCCR_THREE_ROUTE_READINESS_V1061_REPORT.md；REVIEW_PENDING原字节/锁空闲。\n')
 print(json.dumps(summary))
if __name__=='__main__':main()
