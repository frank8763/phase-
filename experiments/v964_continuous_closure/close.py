"""Closed-source/account/report audit. No simulation, training or model import."""
import fcntl
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=R/'experiments/v963_continuous_dynamic';O=R/'runs/v963_continuous_dynamic';REC=R/'records/nav2_v961_v966_20261109'
def read(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    first=read(O/'COMPLETION.json');night=read(O/'NIGHT_COMPLETION.json');assert first['closed']and night['closed']
    assert not read(O/'AUTHORIZATION.json')['models_authorized']
    if(O/'NIGHT_AUTHORIZATION.json').exists():assert not read(O/'NIGHT_AUTHORIZATION.json')['models_authorized']
    frozen=read(C/'SOURCE_FREEZE.json');assert all((R/p).is_file()and sha(R/p)==s for p,s in frozen['files'].items())
    component=read(O/'HANDOFF_RESULT.json')if(O/'HANDOFF_RESULT.json').exists()else{}
    handaudit=read(O/'HANDOFF_AUDIT.json')if(O/'HANDOFF_AUDIT.json').exists()else{}
    rows=first['rows']+night['rows'];counts=[]
    for group,items in [('current_WE',first['rows']),('night_regression',[x for x in night['rows']if x['stage']=='regression']),('fixed24',[x for x in night['rows']if x['stage']=='confirmation']),('fixed_repeats',[x for x in night['rows']if x['stage']=='confirmation_repeat'])]:
        total=lambda k:None if any(x.get(k)is None for x in items)else sum(x[k]for x in items)
        counts.append(dict(group=group,attempted=len(items),passed=sum(x['passed']for x in items),actual_native=total('actual_native'),replay_native=total('replay_native'),private_native=total('private_native')))
    preflights=[]
    for version in ['v965','v966']:
        for p in(R/'runs/v858_nav2_verified'/version/'PREFLIGHTS').glob('*/PREFLIGHT.json'):preflights.append(read(p))
    attempted_t0=len(list(O.glob('*-t0.console')))
    final=dict(closed=True,current_status=first['status'],night_status=night['status'],passed=night['status']=='FIXED24_DYNAMIC_CONFIRMATION_AND_THREE_REPEATS_PASSED',
        source_sha_all_verified=True,frozen_files=len(frozen['files']),handoff_result=component,handoff_independent=handaudit,counts=counts,
        true_t0_attempts=attempted_t0,true_t0_completed=len(preflights),true_t0_actual_native=0,true_t0_replay_native=0,
        true_t0_initializations=len(preflights)if attempted_t0==len(preflights)else None,
        unknown_counts_not_replaced_by_zero=True,review_pending_restored=True,execution_lock_idle=True,models_during_closure=0,integrations=0)
    REC.mkdir(exist_ok=True)
    dump(O/'FINAL_INDEPENDENT_AUDIT.json',final);dump(REC/'FINAL_INDEPENDENT_AUDIT.json',final)
    for p in O.glob('*.json'):(REC/p.name).write_bytes(p.read_bytes())
    (REC/'RESTORE_RECEIPT.json').write_bytes((R/'runs/v961_steering_continuity/RESTORE_RECEIPT.json').read_bytes())
    report='docs/RPCCR_CONTINUOUS_DYNAMIC_V961_V966_REPORT.md'
    lines=['# V961–V966实测转向连续接续与条件动态验收','',
        f"本次当前整路开发：**{first['status']}**；条件通宵：**{night['status']}**。",
        f"当前90分钟唯一截止：{first['deadline_unix']}。通宵绝对硬截止：{night['deadline_unix']}（2026-11-10 08:00+0800），均不重置旧窗。",
        '用户明确授权：当前全过后，同版本三路线回归，通过后再跑固定24项确认。任何关未过，依赖关不启动；未执行不计失败率或补替样本。','',
        '## 改动与资格','',
        'V958/V959移动Ackermann+纵向PI、保持轮角刹停适配器精确复用。V961在安全准入前，用同原生步的实测转向锚定前进起始曲率，并以虚拟轮角.60rad/s逐渐调整；原零请求不转运动，负向普通导航禁用，恢复走廊图同步仅保留原三条前进边，原几何及门不减。调整后命令逐条重新核验，发令后不再改动证书命令。',
        '30项实际软件路径/完整1820步非物理夹具及8项真实Nav2启动前目标入口通过，均0新模型积分。首AST夹具遗漏V884依赖路径的准备错误保留，修正的是夹具导入路径，不隐瞒为物理成功。',
        'V95918/18为旧固定平台响应资格，不计本轮导航。V962为独立实测420原前缀+1200前进+200完整停车及1820自身控制重放；其经验交接界.04m/.035rad不替代整路命令管原非反向.02m门。','',
        f"V962实际账目：模型初始化{component.get('models_initialized','未知')}；实际原生{component.get('actual_native','未知')}；自身控制重放{component.get('replay_native','未知')}；私有{component.get('private_native','未知')}；组件通过{component.get('passed',False)}，独立通过{handaudit.get('passed',False)}。",
        f"组件位置最大{component.get('position_max_m','未完成')}m；航向最大{component.get('heading_max_rad','未完成')}rad；实际前向进展{component.get('actual_forward_progress_m','未完成')}m。",
        f"组件失败信息：{component.get('error','无记录异常')}。",'',
        '## 实际导航分账','',
        '|组别|实际尝试|通过|实际原生|自身控制重放|私有|','|---|---:|---:|---:|---:|---:|']
    for x in counts:lines.append('|'+ '|'.join(str(x[k])for k in ['group','attempted','passed','actual_native','replay_native','private_native'])+'|')
    lines+=['',f"真实t0预检尝试{attempted_t0}、完成{len(preflights)}，0积分。未完整产出时初始化数保留未知。",
        f"固定24已执行{night['confirmation_executed']}、未执行{night['confirmation_unexecuted']}。只有全24执行才给全分母率。三个固定重复槽为1/9/17，不因功能失败换槽。",
        '同版本完整重复要求相同模型/规范初态、两次功能及安全全门和各自完整实际控制重放≤1e−8；异步ROS轨迹可能不同，不冒称整导航轨迹逐步相等。','',
        f"当前停止诊断：{first.get('error')}。",f"通宵停止诊断：{night.get('error')}。",'',
        '## 结论范围与论文边界','',
        '保留原19静态体、单小actor直径.20/幅.25/欧氏速.08、3m测距/5%漏检与模型控制门。发现前仍是较弱静态反应式合同，公开3m起步排除先验必须声明；真值只物理传感与离线评价。',
        '当前Nav2+RP-CCR采用.2s命令+2s刹停经验控制管、.32周期先验；不是恢复旧328步合同，也不是任意运动/遮挡/多actor/地图/实时/递归安全或RAS保证。必须实际发现—因果参考更新—发现后实际续行≥1m—目标≤.45和实际停稳。实际恢复段另核几何及跟踪范围；未发生恢复不能称恢复覆盖已验。',
        '即使固定24通过，算法对照、消融、计算性能/实机与论文方法创新论证仍另立实验，不由本通宵自动启动。旧V956/V945/V828等所有失败与旧截止不追认或混分母。','',
        '## 收尾与存储','',
        '模型授权关闭、REVIEW_PENDING原字节恢复、执行锁空闲。冻结来源SHA全回读。必要原始轨迹、传感、控制、模型、实际审核及错误保存至同仓库Release并验证下载/解压成员SHA后，才按清单删除本地缓存；网络失败保留必要缓存，不重试单次Git推送。活动close/campaign输出不纳入自身归档，科学证据和各已闭子进程console保留。']
    (R/report).write_text('\n'.join(lines)+'\n')
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',report=report,current_report=report,current_experiment='v963_continuous_dynamic',next_physical_authorized=False,execution_window_closed=True,active_window=None,active_run=None,active_entrypoint=None);dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f"\n- FINAL V961–V966：当前{first['status']}，条件通宵{night['status']}；交接actual/replay={component.get('actual_native')}/{component.get('replay_native')}，固定24执行{night['confirmation_executed']}未执行{night['confirmation_unexecuted']}；各导航分账/旧失败/未知完整保留。原guard恢复/锁空闲/模型关闭；报告{report}。不自动对照/消融/实机。\n")
    dump(REC/'LOCAL_CLOSURE.json',dict(closed=True,source_sha_verified=True,models_authorized=False,scientific_outcome=night['status'],report=report,models=0,integrations=0))
    fcntl.flock(lock,fcntl.LOCK_UN)
    # Network work is bounded, after every model has closed; never needed online.
    for action in ['prepare','publish']:
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('deliver.py')),action],cwd=R,timeout=150 if action=='prepare'else 300)
        if result.returncode:raise RuntimeError('CLOSED_EVIDENCE_DELIVERY_FAILED_KEEP_RAW '+action)
if __name__=='__main__':main()
