"""One independently registered speed/brake schedule candidate; never edits old science."""
import ast,datetime,json,shutil,time
from pathlib import Path
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/timed_escape_night_20261105'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
assert read(repo/'runs/forward_escape_night_20261105/LEDGER.json')['closed']and(repo/'REVIEW_PENDING').exists()
authpath=repo/'RPCCR_TIMED_ESCAPE_NIGHT_AUTHORIZATION_20261105.json';assert not authpath.exists()
auth=dict(user_instruction='接着将动态的跑出来，然后明天进入算法对照；继续通宵',authorized_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),absolute_deadline_unix=1793923200.,hard_stop_beijing='2026-11-06T08:00:00+08:00',all_old_failures_windows_immutable=True,new_independent_continuation=True,max_scientific_candidates=1,post_freeze_repairs=0,
 hypothesis='V831 fixed160 brake timing did not materially extend displacement; jointly certify finite speed/brake schedules and full-tail public-goal progress instead of arbitrarily keeping160.',
 wheel_grid=[4.,6.,8.,10.,12.],brake_native_grid=[160,176,192,208,224,240],excluded_duplicate=[4.,240],steer_count=5,new_tail_count=145,old_tail_count=21,complete_tail_native=328,required_new_tail_goal_gain_m=.02,return_only=True,
 component_fixed_states=[495,527],component_cap_s=1800,private_native_cap=1000000,old_replay_native=4216,component_native_cap=656,complete_component_repeat_native_cap=656,
 navigation_main_max=5,conditional_complete_repeats_max=5,new24_confirmation=0,first_functional_or_safety_evidence_failure_stops=True,nav_public_cap=1200,nav_soft_s=1200,nav_hard_s=1500,nav_outer_s=1505,t0_internal_s=120,t0_outer_s=125,
 only_run_phase_models=True,single_cpu_execution_lock=True,training_updates=0,SAC=0,real_robot=0,stage_access=0,subagents=0,chat_monitor=False,network_calls=0,raw_deleted=False,
 comparison='Tomorrow prepared matched algorithm comparison only after full dynamic development/repeat; no automatic comparison before prerequisites. All previous failures preserved.')
assert time.time()+24000<auth['absolute_deadline_unix'];dump(authpath,auth);dump(root/'LEDGER.json',dict(status='PREPARING',closed=False,absolute_deadline_unix=1793923200,candidates_started=0,active_simulation=False,comparison_started=False))
oldcommon=repo/'experiments/forward_escape_night_20261105';oldprobe=repo/'experiments/v831_forward_escape_qualification';oldscience=repo/'experiments/v832_forward_escape_development';probe=repo/'experiments/v833_timed_escape_qualification';science=repo/'experiments/v834_timed_escape_development'
replacements=[('forward_escape_night_20261105','timed_escape_night_20261105'),('v831_forward_escape_qualification','v833_timed_escape_qualification'),('v832_forward_escape_development','v834_timed_escape_development'),('RPCCR_FORWARD_ESCAPE_NIGHT_AUTHORIZATION_20261105.json','RPCCR_TIMED_ESCAPE_NIGHT_AUTHORIZATION_20261105.json'),('RPCCR_FORWARD_ESCAPE_NIGHT_20261105','RPCCR_TIMED_ESCAPE_NIGHT_20261105'),('RPCCR_FORWARD_ESCAPE_V831','RPCCR_TIMED_ESCAPE_V833'),('RPCCR_FORWARD_ESCAPE_V832','RPCCR_TIMED_ESCAPE_V834'),('V831','V833'),('V832','V834')]
for src,dst in[(oldcommon,common),(oldprobe,probe),(oldscience,science)]:
 if dst!=common:assert not dst.exists();dst.mkdir()
 for p in src.iterdir():
  if not p.is_file()or p.suffix not in['.py','.md','.json']or p.name in['INPUT_FREEZE.json','CANDIDATE_FREEZE.json','prepare.py','freeze.py','verify_ops.py']:continue
  s=p.read_text()
  for a,b in replacements:s=s.replace(a,b)
  (dst/p.name).write_text(s)
(repo/'runs'/science.name).mkdir()
cfg=read(science/'BATCH.json');cfg.update(label=science.name,output='runs/'+science.name,archive='evidence/rpccr_timed_escape_v834_20261105');dump(science/'BATCH.json',cfg)
p=science/'reserved_recovery.py';s=p.read_text();s=s.replace('self.allow_forward_escape=False','self.allow_forward_escape=False;self.escape_goal_xy=None')
s=s.replace("escape=[(steer,wheel)for steer in [-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]for wheel in [8.,12.]]", "escape=[(steer,(wheel,brake))for steer in [-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]for wheel in [4.,6.,8.,10.,12.]for brake in [160,176,192,208,224,240]if(wheel,brake)!=(4.,240)]")
s=s.replace("('RETURN_FORWARD_ESCAPE',escape)","('RETURN_TIMED_ESCAPE',escape)")
s=s.replace("            for steer,wheel in choices:\n                brake_only=", "            for steer,wheel in choices:\n                if library=='RETURN_TIMED_ESCAPE':wheel,escape_brake=wheel;assert self.escape_goal_xy is not None\n                brake_only=")
s=s.replace("'FORWARD_ESCAPE_BRAKE'if library=='RETURN_FORWARD_ESCAPE'", "'FORWARD_TIMED_ESCAPE_BRAKE'if library=='RETURN_TIMED_ESCAPE'")
s=s.replace("brake_after=240 if kind=='FORWARD_BRAKE'else 160", "brake_after=escape_brake if kind=='FORWARD_TIMED_ESCAPE_BRAKE'else 240 if kind=='FORWARD_BRAKE'else 160")
s=s.replace("'FORWARD_ESCAPE_BRAKE'","'FORWARD_TIMED_ESCAPE_BRAKE'")
s=s.replace("                reason='TIME_CLEARANCE'", "                goal_gain=None if kind!='FORWARD_TIMED_ESCAPE_BRAKE'else float(np.linalg.norm(real.qpos[:2]-self.escape_goal_xy)-np.linalg.norm(trajectory[-1,:2]-self.escape_goal_xy))\n                reason='TIME_CLEARANCE'")
s=s.replace("and signed<.02 else None", "and signed<.02 else'ESCAPE_NO_GOAL_PROGRESS'if goal_gain is not None and goal_gain<.02 else None")
s=s.replace("'signed_displacement_m':signed,'reason':reason", "'signed_displacement_m':signed,'complete_goal_progress_m':goal_gain,'reason':reason")
s=s.replace("score=minimum+.1*(signed if kind in('FORWARD_BRAKE','FORWARD_TIMED_ESCAPE_BRAKE')else-signed)", "score=minimum+.1*(goal_gain if goal_gain is not None else signed if kind=='FORWARD_BRAKE'else-signed)")
s=s.replace("candidate.allow_forward_escape=True", "candidate.allow_forward_escape=True;candidate.escape_goal_xy=np.asarray(metadata['public_goal_xy'],float)")
p.write_text(s)
p=science/'recovery_supervisor.py';s=p.read_text();s=s.replace("'reference_index':index,'return_nominal_rank'", "'reference_index':index,'public_goal_xy':np.asarray(env.goal_xy).tolist(),'return_nominal_rank'");p.write_text(s)
for name in ['audit_run.py','audit_all_tail_geometry.py']:
 p=science/name;s=p.read_text().replace("kind=='FORWARD_ESCAPE_BRAKE'and brake==160 and tuple(target[2:])in[(8.,8.),(12.,12.)]", "kind=='FORWARD_TIMED_ESCAPE_BRAKE'and brake in[160,176,192,208,224,240]and tuple(target[2:])in[(w,w)for w in[4.,6.,8.,10.,12.]]and not(brake==240 and target[2]==4.)")
 p.write_text(s)
# Generalize only the pre-registered finite schedule sizes; actual physics/audit paths remain intact.
for name in ['probe.py','audit_saved.py']:
 p=probe/name;s=p.read_text().replace('360400','1000000').replace("len(detail['candidates'])==31","len(detail['candidates'])==166").replace("'FORWARD_ESCAPE_BRAKE'","'FORWARD_TIMED_ESCAPE_BRAKE'")
 s=s.replace('reserved.allow_forward_escape=True','reserved.allow_forward_escape=True;reserved.escape_goal_xy=np.asarray(protocol[\'goal_xy\'])')
 s=s.replace("len(cs)==31","len(cs)==166").replace('8+320*31','8+320*166')
 s=s.replace("and cache['brake_after_native_ticks']==160", "and cache['brake_after_native_ticks']in[160,176,192,208,224,240]")
 s=s.replace("if tick>=160:desired[2:]=0.","if tick>=cache['brake_after_native_ticks']:desired[2:]=0.")
 if name=='audit_saved.py':
  a=s.index("  for j,c in enumerate(cs[21:]):");b=s.index("  for c in cs:\n",a)
  s=s[:a]+"  for c,(steer,wheel,brake)in zip(cs[21:],[(s,w,b)for s in[-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]for w in[4.,6.,8.,10.,12.]for b in[160,176,192,208,224,240]if(w,b)!=(4.,240)]):\n   assert c['kind']=='FORWARD_TIMED_ESCAPE_BRAKE'and c['library']=='RETURN_TIMED_ESCAPE'and c['brake_after_native_ticks']==brake and c['target_command'][2:]==[wheel,wheel]\n"+s[b:]
  s=s.replace("assert abs(goal_gain-row['complete_goal_progress_m'])<=1e-10 and row['qualified']==(goal_gain>0)","assert abs(goal_gain-row['complete_goal_progress_m'])<=1e-10 and goal_gain>=.02 and row['qualified']==(goal_gain>0)")
 p.write_text(s)
p=common/'component.py';p.write_text(p.read_text().replace('started+1200','started+1800').replace('>=1199','>=1799'))
p=common/'close_ops.py';s=p.read_text().replace('rpccr_overnight_recovery_ops_20261105','rpccr_timed_escape_ops_20261105');p.write_text(s)
p=probe/'finalize.py';p.write_text(p.read_text().replace('rpccr_forward_escape_v831_20261105','rpccr_timed_escape_v833_20261105'))
for d in[common,probe,science]:
 for p in d.glob('*.py'):ast.parse(p.read_text())
print('ONE_NEW_TIMED_ESCAPE_CANDIDATE_PREPARED_SAME0800_STOP')
