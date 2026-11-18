"""Independent fresh24 closure; no old successes or development in denominator."""
from campaign_context import *
from gates import main_gate,final_gate
import fcntl

def main():
 assert not(O/'FINALIZED.json').exists()
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD
 unchanged=source_ok();rows=d['stages'];gate=main_gate(rows);pairs=d.get('complete_repeats',{})
 passed=bool(d['passed']and unchanged and final_gate(rows,pairs))
 assert not any(r.get('parent_inherited')for r in rows)
 auth=read(O/'AUTHORIZATION.json');auth.update(authorized=False,closed=True);dump(O/'AUTHORIZATION.json',auth)
 report=R/'docs/RPCCR_RECONNECTED_FIXED24_V1248_REPORT.md'
 lines=['# V1248 固定24项重新确认','',f'全部确认门通过={passed}；停止原因={d["stop_reason"]}。',
 '科学精确V1246/V1247：原已具备22mm整路储备的成功分支保持；起点缺额外储备时先有完整证书的短入口恢复（原安全门+2mm，计划停车交接+44mm），实际停稳按实测状态和未重置连续影子重规划，后续整路仍+22mm。原实际.15/接触0/控制/完整停车/原安全门保持，新分段合同明确单列，无运行中修订。',
 '原三路线实际资格按未改变的成功分支、三保存成功全数组精确及新槽13实际主+重复独审建立准入，不冒称本确认批新跑了三路线。旧V1237的11成功和V1247开发槽13均未导入新分母。原池已暴露，非新未见泛化样本。',
 '本批24真实t0后原10060001–24/原相位/原序24主，通过全门后固定1/9/17三完整重复。地图、19静态实体、单小actor、原传感漏检、模型和全部门保持；EW为登记北移.10m课程。发现前较弱已知静态反应式合同/3m起步先验，真值仅物理传感和离线评价。',
 '主>=23/24、每路线>=7/8、方向>=11/12、全安全证据门与固定3重复全须；未执行不算失败或全分母率。首安全/证据/源/控制/操作异常停，只有完整停稳、完整重放和独审合格的限定功能拒绝可以容许一次，第二次停。没有替补/新池/修补。',
 '原生净空>=.15/接触0/全状态控制重放<=1e-8/完整反馈及连续影子/合法ctrl及slew/自体和静态体/根写门全须。新独立10800s双时钟，1200导航/1500含物理回放/310独审/1900启动余时；不延任何旧窗口。',
 '完整主门：`'+json.dumps(gate)+'`。','', '|任务|功能|安全独审|实际原生|自身重放|目标剩余m|错误|','|---|---|---|---:|---:|---:|---|']
 for row in rows:
  r=row.get('result')or{};p=r.get('physical')or{}
  lines.append(f'|{row["stage"]}|{row.get("functional_passed")}|{row.get("safety_evidence_passed")}|{r.get("new_actual_native")}|{r.get("own_replay_native")}|{p.get("goal_distance_m")}|{r.get("error")or r.get("functional_failure")}|')
 lines+=['','固定完整重复：`'+json.dumps(pairs)+'`。','未执行：`'+json.dumps(d.get('unexecuted',[]))+'`。',
 '本批准确或未知计数：`'+json.dumps(d.get('physical_counts'))+'`。未完整插桩的全部普通预测保持unknown，不填0。',
 '开发父V1247计数单列：`'+json.dumps(d.get('parent_physical_counts'))+'`。',
 '用户本轮临时8GiB（包含新父开发和解析资格）/256MiB任务储备，必要证据GitHub备份及SHA流式回读前保留。CPU2idle/单数值线程/GPUhidden/单Phase执行锁/Stage0访问，训练SAC实体0。',
 'REVIEW_PENDING原字节恢复，截止后只零模型收尾。不是任意遮挡/多actor/未知地图/实时/递归保证/实机或RAS全面优势证明。']
 report.write_text('\n'.join(lines)+'\n')
 closed=dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,source_unchanged=unchanged,
  stop_reason=d['stop_reason'],physical_counts=d.get('physical_counts'),report=str(report.relative_to(R)),confirmation_rows_imported=0)
 dump(O/'CLOSED_LEDGER.json',closed)
 current=read(R/'CURRENT_EXPERIMENT.json');assert current.get('active_run')in[None,str(O.relative_to(R))]
 current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,
                latest_report=closed['report'],latest_v1248=closed);dump(R/'CURRENT_EXPERIMENT.json',current)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1248新固定24闭批：passed={passed}，开始{gate["executed"]}/成功{gate["successes"]}，完整24分母={gate["full24_executed"]}，stop={d["stop_reason"]}；0旧确认导入。{report.relative_to(R)}。\n')
 excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'}
 paths={p for root in[C,O,RAW]if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and'__pycache__'not in p.parts and p.name not in excluded};paths.add(report)
 files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)}
 dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True))
 assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
 dump(O/'FINALIZED.json',dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,source_unchanged=unchanged,
   manifest_readback=True,files=len(files),bytes=sum(v['bytes']for v in files.values()),guard_original=True,remote_verified=False))
 print(json.dumps(closed))
if __name__=='__main__':main()
