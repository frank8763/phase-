"""Bounded saved-evidence diagnosis of the V848 west-east progress cycle; zero models."""
import importlib.abc
import sys


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('DIAGNOSIS_FORBIDS_MODELS')


sys.meta_path.insert(0,NoModels())
import collections
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
OUT=R/'runs/v849_saved_cycle_diagnosis'
CELL=R/'runs/v848_goal_first_worker/v848_main_slot01/paired/geometry_memory'


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_DIAGNOSIS_180S_CAP')));signal.alarm(180)
    OUT.mkdir(parents=True,exist_ok=True);guard=(R/'REVIEW_PENDING').read_bytes()
    with(R/'runs/v648_static_unknown/execution.lock').open('rb')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    inputs=set()
    def read(p):inputs.add(p);return json.loads(p.read_text())
    def lines(p):inputs.add(p);return[json.loads(s)for s in p.open()]
    def gz(p):
        inputs.add(p)
        with gzip.open(p,'rt')as stream:return json.load(stream)
    protocol=read(CELL.parent/'STATIC_PROTOCOL.json');goal=np.asarray(protocol['goal_xy'])
    execution=lines(CELL/'v648_execution.jsonl');admissions=lines(CELL/'model_admission.jsonl')
    xy=np.asarray([r['qpos_full'][:2]for r in execution]);distance=np.linalg.norm(xy-goal,axis=1)
    old={r['activation_step']:r for r in[gz(p)for p in sorted((CELL/'recovery_contracts').glob('*.json.gz'))]}
    handovers=[]
    for p in sorted((CELL/'handover_certificates').glob('*.json.gz')):
        new=gz(p);step=new['handover_step'];contract=max((v for k,v in old.items()if k<step),key=lambda v:v['activation_step'])
        assert contract['created_step']==new['old_created_step']
        cursor=new['old_native_cursor'];entry=np.asarray(new['real_entry_qpos']);qv=np.asarray(new['real_entry_qvel'])
        err=max(float(np.max(abs(entry-np.asarray(contract['qpos'])[cursor-1]))),float(np.max(abs(qv-np.asarray(contract['qvel'])[cursor-1]))))
        assert err<=1e-8
        before=float(np.linalg.norm(entry[:2]-goal));old_goal=float(np.linalg.norm(np.asarray(contract['qpos'])[-1,:2]-goal));new_goal=float(np.linalg.norm(np.asarray(new['qpos'])[-1,:2]-goal))
        handovers.append(dict(step=step,old_activation_step=contract['activation_step'],old_native_cursor=cursor,
            nominal_240_goal_gain_m=new['metadata']['predicted_goal_progress_m'],
            old_remaining_certificate_goal_gain_m=before-old_goal,new_complete328_goal_gain_m=before-new_goal,
            current_goal_m=before,old_terminal_goal_m=old_goal,new_terminal_goal_m=new_goal,
            actual_first8_goal_gain_m=before-float(distance[step]),
            old_kind=contract['recovery_kind'],new_kind=new['recovery_kind'],
            old_minimum_m=contract['minimum_causal_predicted_clearance_m'],new_minimum_m=new['minimum_causal_predicted_clearance_m'],
            new_proactive=new['proactive_joint'],state_join_error=err))
    assert len(handovers)==14 and all(x['nominal_240_goal_gain_m']>=.02 and x['new_complete328_goal_gain_m']<0 and not x['new_proactive']for x in handovers)
    assert handovers[0]['old_remaining_certificate_goal_gain_m']>0 and handovers[0]['old_kind']=='FORWARD_BRAKE'
    ordinary=[]
    for row in admissions:
        if row['status']!='MODEL_SAFE_COMMAND'or row.get('certified_backup_handover'):continue
        step=row['step'];p=CELL/'ordinary_certificates'/f'certificate_{step:04d}.npz';inputs.add(p)
        with np.load(p)as z:end=z['qpos'][-1,:2]
        before=float(np.linalg.norm(np.asarray(execution[step-1]['qpos_full']if step else protocol['start_qpos'])[:2]-goal))
        ordinary.append(dict(step=step,early=row.get('early_joint_selection',False),complete_goal_gain_m=before-float(np.linalg.norm(end-goal)),actual_first8_goal_gain_m=before-float(distance[step])))
    early=[x for x in ordinary if x['early']]
    assert early and all(x['complete_goal_gain_m']>=.02-1e-10 for x in early)
    revalidation=[r for r in lines(CELL/'route_revalidation.jsonl')if r['step']>=917]
    replay=read(CELL.parent/'NATIVE_REPLAY_AUDIT.json');matches=lines(CELL/'reserved_state_matches.jsonl')
    max_prefix_error=max(max(row['maximum_qpos_error'],row['maximum_qvel_error'],row['maximum_ctrl_error'])for row in matches)
    ns=read(R/'runs/v848_goal_first_worker/v848_main_slot02/paired/geometry_memory/result.json')
    result=dict(status='SAVED_CAUSE_WITNESSES_VERIFIED_NO_ALGORITHM_FIX',
        handovers=handovers,nominal_positive_but_complete_negative_handovers=len(handovers),
        new_return_tail_kinds=dict(collections.Counter(x['new_kind']for x in handovers)),
        ordinary_certificates=len(ordinary),ordinary_complete_goal_negative=sum(x['complete_goal_gain_m']<-.001 for x in ordinary),
        early_joint_certificates=len(early),early_joint_actual_first8_negative=sum(x['actual_first8_goal_gain_m']<-.000001 for x in early),
        late_route_checks=len(revalidation),late_stagnation_triggers=sum(r['stagnated_without_route_progress']for r in revalidation),
        last300_sampled_travel_m=float(np.linalg.norm(np.diff(xy[-300:],axis=0),axis=1).sum()),
        last300_net_goal_progress_m=float(distance[-300]-distance[-1]),maximum_executed_prefix_prediction_error=max_prefix_error,
        full_native_replay_error=replay['maximum_full_native_state_ctrl_error'],north_south_recovery_activations=ns['reserved_recovery_activations'],
        conclusion='Return progress is screened on a nominal240 trajectory; complete328 admission certifies a different prefix-plus-backup sequence without the proactive progress filter. All14 accepted returns have nominal gain but goal-regressing complete certificates. Short-window motion/route-arc stagnation does not flag the resulting cycle.',
        limitation='Saved certificates and exact original policy replay identify an exercised selection defect. They do not demonstrate that any proposed repair completes the full route.',
        models=0,integrations=0,new_navigation=0,old_failures_unchanged=True)
    (OUT/'ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    # Reproduce the actual supervisor's acceptance, with saved native providers; expected RED.
    run=subprocess.run([sys.executable,'-B',str(C/'replay_policy.py'),'--assert-progress-consistency'],cwd=R,capture_output=True,text=True,timeout=180)
    (OUT/'POLICY_RED_FEEDBACK.console').write_text(run.stdout+run.stderr)
    assert run.returncode!=0 and'ACTUAL_RETURN_POLICY_ACCEPTS_GOAL_REGRESSING_CERTIFICATE'in run.stderr
    for p in [*C.glob('*.py'),R/'experiments/v848_goal_first_worker/recovery_supervisor.py',R/'experiments/v848_goal_first_worker/reserved_recovery.py',R/'experiments/v848_goal_first_worker/joint_admission.py']:inputs.add(p)
    hashes={}
    for p in sorted(inputs):
        h=hashlib.sha256()
        with p.open('rb')as stream:
            for b in iter(lambda:stream.read(4*1024**2),b''):h.update(b)
        hashes[str(p.relative_to(R))]=h.hexdigest()
    (OUT/'INPUT_SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n')
    assert(R/'REVIEW_PENDING').read_bytes()==guard
    report=R/'docs/RPCCR_V848_CYCLE_CAUSE_20261107.md'
    report.write_text('''# V848 东西路线未到达的保存证据诊断

核心缺口在后备返回与普通动作回退分支的进展定义。名义240原生步预测能接近目标，实际获得安全许可的是另一条8+320控制序列；后者可能以倒退避险结束。返回判据把前者的进展当成了后者可持续执行的进展。

14次返回的名义预测增益全部>=.02m，但完整获证序列的终点目标增益全部<0；13次REVERSE_BRAKE、1次BRAKE_ONLY。第573步当前距目标1.680784m，原先仍适用的前向尾预测终点1.444583m（可进展.236201m，最低净空.158885）；替换后的完整证书预测终点1.830857m（倒退.150073m，最低净空.155925），仅因为名义预测声称前进.179287m就返回成功。旧尾当前状态与新证书入口全状态连接误差0。

源调用链：recovery_supervisor.py只对名义trajectory[-1]施加.02进展门；ReservedRecovery.try_handover重新构造默认proactive=False的候选；admit_nominal中全尾目标进展过滤仅在proactive/following激活，因此该返回分支没有同一条完整证书的进展比较。普通admit_ranked在提前联合选择失败后也会回到原安全尾筛选，缺少同样的任务进展要求。安全证书仍有效，问题是安全可退与任务可前进没有统一。

此次新early_joint分支的445个保存证书均满足原整尾目标进展门，实际首8原生没有一项目标负进展；主要问题并非该新分支的首前缀全部倒走。南北路线0次后备激活，东西路线14次激活，正好暴露了尚未覆盖的旧返回/回退分支。这个比较是已观察任务的机制证据，不是统计泛化或单因素优势证明。

循环检测也存在缺口：最后300公开步位置累计3.899132m，净目标进展.000175m；第917步及以后215次路线检查的stagnated_without_route_progress均为false。现有条件关注30步位移/航向和局部路线弧长，车辆持续往返时仍会被当作有运动进展。

全原生重放和已执行首前缀状态控制预测误差均0，12次全局规划均返回完整目标参考。当前证据将主因定位到控制分支的进展判据不一致和反复切换，未显示执行状态漂移。部分普通前向候选确实被原完整未来安全门拒绝；不能以此次失败为由降低.155/.15或缩短328时长。

修订方向：返回时评价实际新联合证书的任务进展，并与仍适用的旧证书剩余进展比较；普通回退与返回共用这一进展语义。必要的倒车避险应有独立阶段和可核验续接，不能一律禁倒车，也不能把暂时可退叫作正常推进。增加针对重复恢复序列和较长尺度净任务进展的循环检测。先用第573步反例及其余13次真实返回作保存资格，再另立有界原生验证；尚未修改算法或证明修订后全程成功。

可复现命令：`python3 -B experiments/v849_saved_cycle_diagnosis/replay_policy.py --assert-progress-consistency`。实际调用原RecoverySupervisor，预测器和证书提供者只返回已有保存结果，不加载/重演物理；预期RED为ACTUAL_RETURN_POLICY_ACCEPTS_GOAL_REGRESSING_CERTIFICATE。真实旧安全证书来自已完成原生审核，本诊断不冒称新物理验证。

本次模型初始化/积分/导航/训练全部0，旧源/协议/失败/截止保持，REVIEW_PENDING原字节未改。
''')
    print(json.dumps({k:v for k,v in result.items()if k!='handovers'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
