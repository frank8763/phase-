"""Pre-freeze assembly only. Never invokes a model."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[2];W=R/'experiments/v841_early_joint';C=Path(__file__).parent
p=W/'helpers.py';s=p.read_text().replace("root=repo/'runs/v841_early_joint'","root=repo/'runs/v841_early_joint/qualification'");p.write_text(s)
p=W/'early_joint.py';s=p.read_text().replace("np.linalg.norm(q[:2]-goal)","np.linalg.norm(q[:2]-goal)")
# expected is the state AFTER the admitted 8 native steps, never the pre-command state.
s=s.replace("np.asarray(cache['initial_qpos']).copy();reserved.last_prefix_qvel", "np.asarray(cache['initial_qpos']).copy();reserved.last_prefix_qvel")
p.write_text(s)
p=W/'reserved_recovery.py';s=p.read_text();duplicate="                controls=extended['controls'][:320].copy()if active else self.controls(target,proposal,brake_after)\n";s=s.replace(duplicate+duplicate,duplicate);p.write_text(s)
p=W/'qualify_probe.py';s=p.read_text().replace('>495','>295').replace('==496','==296').replace('[490,495]','[295]').replace('500000','200000').replace('3960','2360')
a=s.index(" with gzip.open(next((cell/'recovery_contracts')")
b=s.index("  row=dict(step=step",a)
s=s[:a]+''' for entry in entries:
  step=entry['step'];folder=root/f'step{step:04d}';folder.mkdir();mujoco.mj_copyData(d,m,snapshots[step]);initial=full(d).copy();state=entry['state'];field=SimpleNamespace(**static.__dict__);field.pose_values=MethodType(pose_values,field);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);selected=None;attempts=[]
  from early_joint import activate,select
  reserved=ReservedRecovery(predictor,mujoco,ids,folder);reserved.public_goal_xy=np.asarray(protocol['goal_xy']);reserved.cache={'minimum_causal_predicted_clearance_m':entry['previous_reserve_minimum_m'],'created_step':294}
  reference=np.asarray(entry['reference']['path']);index=int(np.argmin(np.linalg.norm(reference[:,:2]-d.qpos[:2],axis=1)));index=min(index,len(reference)-2);reserved.set_reference(reference,index,protocol['goal_xy'],.60)
  assert activate(reserved,state,step)and step==295
  nominal=entry['nominal'];safe=sorted([c for c in nominal['candidates']if c['reason']is None],key=lambda c:c['score'],reverse=True);unique=[];seen=set()
  for c in safe:
   key=tuple(c['first_command'])
   if key in seen:continue
   seen.add(key);z=np.load(cell/'nominal_forecasts'/c['nominal_saved_forecast']);unique.append((c['score'],np.asarray(key),z['poses'],c['minimum_clearance_m'],c['self_domain_margin_m']))
  prefixes={};admit=reserved.admit_nominal
  def capture(*args):
   samples.clear();summary=admit(*args);prefixes[tuple(args[1])]=copy.deepcopy(samples);return summary
  reserved.admit_nominal=capture
  chosen=select(reserved,predictor,d,nominal['summary'],field,state,step,reference,index,folder,unique)
  assert np.array_equal(full(d),initial),'PRIVATE_PREDICTION_MUTATED_REAL'
  event=json.loads((folder/'early_joint_decisions.jsonl').read_text());attempts=event['probes'];dump(folder/'ATTEMPTS.json',attempts)
  if chosen is not None:
   command,gate,summary=chosen;proposal={'command':command.tolist(),'rank':gate['joint_admission_distinct_command_rank']};samples[:]=prefixes[tuple(command)];selected=(proposal,reserved)
''' +s[b:]
s=s.replace("complete_goal_progress_m=gain))","complete_goal_progress_m=gain))")
s=s.replace("status='FIXED_ESCAPE_COMPONENTS_EVALUATED'","status='EARLY_JOINT_COMPONENT_EVALUATED'")
p.write_text(s)
# Replace only the legacy component-selection audit; calibration/physical/coverage verification remains.
p=W/'qualify_audit_saved.py';s=p.read_text().replace('FIXED_ESCAPE_COMPONENTS_EVALUATED','EARLY_JOINT_COMPONENT_EVALUATED').replace('>495','>295').replace('==496','==296').replace('3960','2360')
a=s.index(" step=entry['step'];assert row['step']==step;");b=s.index(" z=np.load(folder/'CERTIFICATE.npz')",a)
s=s[:a]+''' step=entry['step'];assert row['step']==step;folder=root/f'step{step:04d}';event=json.loads((folder/'early_joint_decisions.jsonl').read_text())
 from early_joint_independent import check
 check(folder,event,entry['nominal']['candidates'],protocol,deep=True,source_cell=cell)
 for a in event['probes']:private+=8+328*len(a['detail']['candidates'])
 if not row['component_executed']:
  assert event['selected_rank']is None;rows.append(dict(step=step,qualified=False));continue
 selected=read(folder/'SELECTED.json');cache=selected['cache'];assert event['selected_rank']==selected['proposal']['rank']
 check_successor(cache,protocol,limits,rate)
''' +s[b:]
s=s.replace("==len(entries)==2 and private==result['counts']['private_native']<=500000","==len(entries)==1 and private==result['counts']['private_native']<=200000")
s=s.replace('REFERENCE_RECOVERY_FIXED_NATIVE_INDEPENDENT_PASS','EARLY_JOINT_FIXED_NATIVE_INDEPENDENT_PASS')
p.write_text(s)
p=W/'qualify_finalize.py';s=p.read_text().replace("own/'audit_saved.py'","own/'qualify_audit_saved.py'").replace('固定返回逃离完整尾资格','提前联合完整尾资格').replace('固定490/495、旧3960重放','固定295、旧2360重放').replace('rpccr_reference_recovery_v841_20261106','rpccr_early_joint_v841_qualification_20261106');p.write_text(s)
p=C/'qualify.py';s=p.read_text().replace('len(tasks)==5','len(tasks)==1').replace("len({t['seed']for t in tasks})==5","len({t['seed']for t in tasks})==1").replace("bad=rows[::-1];assert not main_gate(tasks,bad,False)['passed']","bad=[dict(rows[0],task=dict(tasks[0],seed=-1))];assert not main_gate(tasks,bad,False)['passed']").replace('actual5t0_interface_passed','actual1t0_interface_passed');p.write_text(s)
p=C/'finalizer.py';s=p.read_text().replace("combined_three_route_development_passed=combined","single_fixed_scene_development_passed=combined").replace('FIVE_FIXED_DEVELOPMENT_TASKS_AND_REPEATS_VERIFIED','ONE_FIXED_SCENE_AND_COMPLETE_REPEAT_VERIFIED').replace('REFERENCE_FOLLOWING_RECOVERY_WITH_FINITE_SUCCESSOR_336','EARLY_JOINT_NOMINAL_AND_COMPLETE_TAIL_WITH_336_CONTINUATION').replace('两旧失败任务和原三路线全部作为已观察开发样本；各完整重复另计，不混新确认。','原10060002单个旧失败开发样本；成功才同版本完整重复，不混新确认。').replace('原21尾全拒后18个沿原因果参考反馈转向的完整恢复尾','旧证书净空余量低于.155+.08×3.28=.4174时提前联合至多4个原名义首命令与原21及18沿参考完整尾，按完整328净空+.5目标进展选择').replace('普通及返回均适用。','仅普通行驶提前联合；原返回保持不变。');p.write_text(s)
for directory in [W,C]:
 for p in directory.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
print('PRE_FREEZE_SINGLE_STATE_AND_SINGLE_SCENE_ASSEMBLED')
