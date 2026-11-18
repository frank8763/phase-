"""Zero-model closure: parent6 and new18 explicitly separated, no parent rewrite."""
from campaign_context import *
from gates import main_gate,final_gate
import fcntl

def main():
 assert not(O/'FINALIZED.json').exists();f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 d=read(O/'COMPLETION.json');assert d['closed']and sha(R/'REVIEW_PENDING')==GUARD
 auth=read(O/'AUTHORIZATION.json');auth.update(authorized=False,closed=True);dump(O/'AUTHORIZATION.json',auth)
 unchanged=source_ok();rows=d.get('stages',[]);gate=main_gate(rows);passed=bool(d.get('passed')and unchanged and final_gate(rows,d.get('complete_repeats',{})))
 parent=[r for r in rows if r.get('checkpoint_imported')and r['role']=='main'];new=[r for r in rows if not r.get('checkpoint_imported')and r['role']=='main'];assert len(parent)==6
 report=R/'docs/RPCCR_FIXED24_SAME_SCIENCE_RESUME_V1230_REPORT.md'
 lines=['# V1230 同科学固定24跨窗口接续','',f'完整确认通过={passed}；停止原因={d["stop_reason"]}。',
 '科学和模型精确保持V1228。原V1228已闭合，因完整任务及审核余时不足停，旧20:30截止和原NOT_COMPLETED结果保持。用户另授权独立3h，本批只执行原未执行7–24及主门后固定1/9/17；不重跑或替换已通过1–6，不换种子相位、不冻结后改源。',
 f'本合并评估明确为同科学/同原预注册固定池跨窗口完成：父批已独审主6项，本批新增主{len(new)}项。原24t0及4NS开发/2对精确重复继承并单列；非本批新初始化/新主或独立新样本，不与旧版8成功混计。',
 '完整门：`'+json.dumps(gate)+'`。全24未实际执行不报完整分母率。','', '|任务|来源|功能|安全证据独审|实际原生|重放|错误|','|---|---|---|---|---:|---:|---|']
 for row in rows:
  if row['role']=='t0':continue
  r=row.get('result')or{};lines.append(f'|{row["stage"]}|'+('V1228继承'if row.get('checkpoint_imported')else'V1230新增')+f'|{row.get("functional_passed",False)}|{row.get("safety_evidence_passed",False)}|{r.get("new_actual_native")}|{r.get("own_replay_native")}|{r.get("error")or r.get("functional_failure")}|')
 lines+=['','固定重复比较：`'+json.dumps(d.get('complete_repeats',{}))+'`。','未执行：'+str(d.get('unexecuted',[]))+'。','父批准确或未知账目：`'+json.dumps(d.get('checkpoint_parent_counts'))+'`。','本新增准确或未知账目：`'+json.dumps(d.get('physical_counts',dict(unknown=True)))+'`。未知预测不填0。',
 '原任务>=23/24、每路线7/8、方向11/12和全部安全门、固定1/9/17三完整重复<=1e-8全须；重复1对父批main1，不替补。首次安全证据操作异常或第二合格功能失败即停。',
 '父证据已GitHubRelease全压缩及解压成员SHA回读；仅备份后按清单清理父大文件，保留重复1完整基线。原始本批必要证据远端未核验不删。共享父+接续2GiB，256MiB任务前储备，CPU2idle/GPU隐藏/Stage0访问/训练实机0。',
 '这是已暴露固定课程经验性复验；未知地图/任意遮挡/多actor/实时/递归保证/实机/RAS全面优势均未证明。']
 report.write_text('\n'.join(lines)+'\n')
 closed=dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,source_unchanged=unchanged,stop_reason=d['stop_reason'],report=str(report.relative_to(R)),same_science_multi_window_completion=True,parent_main_imported=6,new_main_started=len(new),physical_counts_new_only=d.get('physical_counts'),physical_counts_parent_separate=d.get('checkpoint_parent_counts'))
 dump(O/'CLOSED_LEDGER.json',closed)
 j=read(R/'CURRENT_EXPERIMENT.json');assert j.get('active_run')in[None,str(O.relative_to(R))];j.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=closed['report'],latest_v1230=closed);dump(R/'CURRENT_EXPERIMENT.json',j)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f'\n- V1230同科学原固定24跨窗接续闭批：passed={passed}，父6主继承/新增{len(new)}主，合并{gate["successes"]}/{gate["executed"]}已执行，原24全分母={gate["full24_executed"]}，stop={d["stop_reason"]}；原V1228闭批及20:30不改，不冒称新池/独立新样本。{report.relative_to(R)}。\n')
 excluded={'LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','watchdog_finalize.console'};paths={p for root in[C,O,RAW]if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.name not in excluded};paths.add(report)
 files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)};dump(O/'LOCAL_MANIFEST.json',dict(files=files,remote_verified=False,raw_retained=True,parent_remote_index='records/nav2_v1228_checkpoint_20261116/REMOTE_VERIFIED.json'));assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
 dump(O/'FINALIZED.json',dict(closed=True,fixed24_confirmation_passed=passed,main_gate=gate,source_unchanged=unchanged,manifest_readback=True,files=len(files),bytes=sum(v['bytes']for v in files.values()),remote_verified=False,guard_original=True,same_science_multi_window_completion=True,closed_unix=time.time()));print(json.dumps(closed))
if __name__=='__main__':main()
