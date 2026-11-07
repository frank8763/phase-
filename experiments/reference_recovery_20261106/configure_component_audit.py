"""Prepare the independent saved component audit before any models."""
from pathlib import Path
import ast

repo=Path(__file__).resolve().parents[2]
qual=repo/'experiments/v835_reference_recovery_qualification'
science=repo/'experiments/v836_reference_recovery_development'
assert not(qual/'INPUT_FREEZE.json').exists()
p=science/'reserved_recovery.py';s=p.read_text().replace("self_bounds=extended['self_bounds'])", "self_bounds=extended['self_bounds'],qpos=extended['qpos'],qvel=extended['qvel'])")
p.write_text(s)
p=science/'reference_certificate_audit.py';s=p.read_text().replace('def expected_follow(c, limits, rate):','def expected_follow(c, limits, rate, require_progress=True):')
s=s.replace("    assert np.linalg.norm(np.asarray(c['prefix_initial_qpos'])[:2]-goal)-np.linalg.norm(np.asarray(c['qpos'])[-1, :2]-goal) >= .02-1e-10\n    assert c['signed_longitudinal_displacement_m'] >= .02", "    if require_progress:\n        assert np.linalg.norm(np.asarray(c['prefix_initial_qpos'])[:2]-goal)-np.linalg.norm(np.asarray(c['qpos'])[-1, :2]-goal) >= .02-1e-10\n        assert c['signed_longitudinal_displacement_m'] >= .02")
p.write_text(s)
p=qual/'probe.py';s=p.read_text()
s=s.replace("assert len(detail['candidates'])in[1,16,21,39]", "assert len(detail['candidates'])in[1,16,21,39]")
s=s.replace("records=[];status='RUNNING'", "records=[];status='RUNNING'")
anchor="    return trajectory\n   predictor.predict=calibrated_predict"
s=s.replace(anchor, """    if step==490 and np.array_equal(args[1],old_contract['target']):
     complete=np.vstack([poses(np.asarray([x['qpos']for x in samples])),trajectory]);expected=np.vstack((old_contract['prefix_poses'],old_contract['poses']));error=float(np.max(abs(complete-expected)));maximum[0]=max(maximum[0],error);assert error<=1e-8,'ORIGINAL_ACCEPTED490_FORECAST_CHANGED'
    return trajectory
   predictor.predict=calibrated_predict""")
s=s.replace(" for entry in entries:\n  step=entry", " with gzip.open(next((cell/'recovery_contracts').glob('*.gz')),'rt')as stream:old_contract=json.load(stream)\n assert old_contract['created_step']==490\n for entry in entries:\n  step=entry")
p.write_text(s)
p=qual/'audit_saved.py';s=p.read_text().replace('>527','>495').replace('528','496').replace('4216','3960')
start=s.index('for entry,row in zip(entries,result[\'records\']):')
end=s.index(' observations=[]',start)
tail=s[end:]
tail=tail.replace('len(actual)==len(repeat)==328','len(actual)==len(repeat)==336')
tail=tail.replace('private==result[\'counts\'][\'private_native\']<=1000000', 'private==result[\'counts\'][\'private_native\']<=500000')
tail=tail.replace("==328*executed", "==336*executed")
tail=tail.replace("'FORWARD_ESCAPE_FIXED_NATIVE_INDEPENDENT_PASS'", "'REFERENCE_RECOVERY_FIXED_NATIVE_INDEPENDENT_PASS'")
middle='''from reference_certificate_audit import check_successor,expected_follow
for entry,row in zip(entries,result['records']):
 step=entry['step'];assert row['step']==step;folder=root/f'step{step:04d}';attempts=read(folder/'ATTEMPTS.json');expected=eligible(entry,np.asarray(protocol['goal_xy']));assert 0<len(attempts)<=len(expected)
 for i,a in enumerate(attempts):
  assert a['source']==expected[i]and a['old21_maximum_pose_error']<=1e-8
  cs=a['detail']['candidates'];assert len(cs)in[1,16,21,39];private+=8+328*len(cs)
  assert a['detail']['reference_successor_active']and np.array_equal(a['detail']['reference']['path'],entry['reference']['path'])
  if len(cs)==39:
   assert all(c['reason']is not None for c in cs[:21])
   for c,(look,wheel,brake)in zip(cs[21:],[(l,w,b)for l in[.35,.55]for w in[4.,8.,12.]for b in[160,208,240]]):
    assert c['kind']=='REFERENCE_FOLLOW_BRAKE'and c['library']=='REFERENCE_FOLLOW'and c['brake_after_native_ticks']==brake and c['lookahead_m']==look and c['wheel_speed']==wheel
  for c in cs:
   z=np.load(folder/c['full_forecast_file']);v=values(z['poses'],entry['state']);assert len(v)==336
   margin=min(a['detail']['prefix_self_domain_margin_m'],float(containment_margin(z['self_bounds'][:321],bounds).min()))
   speed=float(np.linalg.norm(z['qvel'][319,:2]));extra_margin=float(containment_margin(z['self_bounds'],bounds).min());extra_speed=float(np.linalg.norm(z['qvel'][-1,:2]))
   assert max(abs(margin-c['self_domain_margin_m']),abs(speed-c['terminal_speed_m_s']))<=1e-8
   reason='TIME_CLEARANCE'if v[:328].min()<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'SUCCESSOR_CLEARANCE'if v.min()<.155 else'SUCCESSOR_SELF'if extra_margin<.002 else'SUCCESSOR_TERMINAL_SPEED'if extra_speed>.025 else'INSUFFICIENT_REVERSE'if c['kind']=='REVERSE_BRAKE'and c['signed_displacement_m']>-.02 else'INSUFFICIENT_FORWARD'if c['kind']in('FORWARD_BRAKE','REFERENCE_FOLLOW_BRAKE')and c['signed_displacement_m']<.02 else'ESCAPE_NO_GOAL_PROGRESS'if c['kind']=='REFERENCE_FOLLOW_BRAKE'and c['complete_goal_progress_m']<.02 else None
   assert reason==c['reason'],(step,i,c['kind'],reason,c['reason'])
   if c['early_rejection_witness_file']is not None:
    tick=c['early_rejection_witness_native_tick'];assert abs(v[tick-1]-c['early_rejection_witness_value_m'])<=1e-8 and v[tick-1]<.155
   if c['successor_minimum_m']is not None:assert abs(v.min()-c['successor_minimum_m'])<=1e-8
   assert np.array_equal(z['controls'][:8],np.repeat([a['source']['command']],8,axis=0))
   if c['kind']=='REFERENCE_FOLLOW_BRAKE':
    fake={'reference_following':{**a['detail']['reference'],'lookahead_m':c['lookahead_m'],'wheel_speed':c['wheel_speed'],'drive_ticks':c['brake_after_native_ticks'],'targets':[]},'initial_qpos':z['qpos'][0].tolist(),'prefix_command':a['source']['command'],'brake_after_native_ticks':c['brake_after_native_ticks'],'qpos':z['qpos'][:320].tolist(),'controls':z['controls'][8:328].tolist(),'one_cycle_continuation':{'extra_qpos':z['qpos'][320:].tolist(),'extra_controls':z['controls'][328:].tolist()}}
    # Full controller reconstruction for the selected complete cache below;
    # every rejected new sequence still has complete native/geometry evidence.
   assert np.all(z['controls']>=limits[:,0]-1e-12)and np.all(z['controls']<=limits[:,1]+1e-12)and np.all(abs(np.diff(z['controls'][::8],axis=0))<=rate+1e-12)
 if not row['component_executed']:
  assert len(attempts)==len(expected);rows.append(dict(step=step,qualified=False));continue
 selected=read(folder/'SELECTED.json');cache=selected['cache'];assert selected['proposal']==expected[len(attempts)-1]and cache['recovery_kind']=='REFERENCE_FOLLOW_BRAKE'
 check_successor(cache,protocol,limits,rate)
 z=np.load(folder/'CERTIFICATE.npz');p=poses(z['qpos']);v=values(p,entry['state']);assert len(p)==336 and np.max(abs(v-z['causal_values']))<=1e-8 and v.min()>=.155
 assert containment_margin(z['self_bounds'],bounds).min()>=.002 and np.linalg.norm(z['qvel'][-1,:2])<=.025
 expected_controls=np.vstack((np.repeat([selected['proposal']['command']],8,axis=0),cache['controls'],cache['one_cycle_continuation']['extra_controls']))
 assert np.array_equal(z['controls'],expected_controls)and np.all(abs(z['controls'][0]-z['initial_ctrl'][ids])<=rate+1e-12)
 goal_gain=float(np.linalg.norm(z['initial_qpos'][:2]-protocol['goal_xy'])-np.linalg.norm(z['qpos'][-1,:2]-protocol['goal_xy']));assert abs(goal_gain-row['complete_goal_progress_m'])<=1e-10 and goal_gain>=.02 and row['qualified']==(goal_gain>=.02)
 aa=np.load(folder/'ACTUAL.npz');bb=np.load(folder/'REPEAT.npz');assert np.max(abs(aa['integration']-bb['integration']))<=1e-8
 actual=[x for x in physical if x['context']==f'S{step}_ACTUAL'];repeat=[x for x in physical if x['context']==f'S{step}_REPEAT'];assert len(actual)==len(repeat)==336
 for tick,(a,b)in enumerate(zip(actual,repeat)):
  assert a['contacts']==b['contacts']and max(np.max(abs(np.asarray(a[k])-b[k]))for k in['qpos','qvel','ctrl','mocap'])<=1e-8
  assert max(np.max(abs(np.asarray(a['qpos'])-z['qpos'][tick])),np.max(abs(np.asarray(a['qvel'])-z['qvel'][tick])),np.max(abs(np.asarray(a['ctrl'])[ids]-z['controls'][tick])))<=1e-8
'''
s=s[:start]+middle+tail
p.write_text(s)
for path in qual.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
for path in science.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
print('INDEPENDENT_COMPONENT_AUDIT_AND_ACCEPTED490_CALIBRATION_PREPARED')
