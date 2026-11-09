"""Regression against recorded V914 refusal and independent full-phase envelope.
No simulator, physical initialization, ROS or learned policy imports.
"""
import ast,copy,gzip,hashlib,importlib.abc,json,math,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v916_cycle_backup';S=O/'saved/runs/v858_nav2_verified/v914/main_we'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','vehicle','factory','physical','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static'),str(R/'experiments/v884_feasible_rpp')]
from cycle_backup import cycle_upper,terminal_bound,retained_allowed
from command_tube import admit
from periodic_support import swept_bounds
from handshake import require
rows=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()));known=json.loads((S/'physics/SETUP.json').read_text())['known']
last=rows[-1];old=rows[-2]['proof'];checks={};proof=admit(last['packet'],last['source'],0,0,known,last['proof']['issued_at'])
checks['original_fresh_zero_refusal_reproduced']=not last['proof']['passed']and abs(last['proof']['dynamic_lower_m']-.15223815582335348)<1e-10 and not proof['passed']and proof['terminal_cycle_lower_m']<.155
checks['old_finite_tail_remains_valid']=retained_allowed(old,.04)
checks['old_finite_tail_not_extended']=not retained_allowed(old,2.4)
for name,elapsed in [('negative_elapsed',-1),('nan_elapsed',float('nan'))]:checks[name]=not retained_allowed(old,elapsed)
checks['failed_proof_cannot_retain']=not retained_allowed(dict(old,passed=False),.01)
checks['forged_cycle_boolean_cannot_extend']=not retained_allowed(dict(old,terminal_cycle_qualified=True,terminal_cycle_lower_m=.154),10)
checks['nan_cycle_cannot_extend']=not retained_allowed(dict(old,terminal_cycle_qualified=True,terminal_cycle_lower_m=float('nan')),10)
checks['missing_cycle_cannot_extend']=not retained_allowed(dict(old,terminal_cycle_qualified=True),10)
checks['stale_body_cannot_retain']=not retained_allowed(dict(old,body_age_s=.051),.01)
# Independently compare every saved coefficient set with the original trig extrema.
errors=[];dense=0;changed=0;safe=None
for row in rows:
 prior=row['source'].get('periodic')
 if prior is None:continue
 upper=cycle_upper(prior);t=row['source']['source_scan_sim_time'];independent=swept_bounds(prior['vertices'],t,t+2*math.pi/.32);errors.append(float(abs(upper-independent).max()))
 # Each vertex must be bounded on an independent dense full-period grid.
 at=t+np.linspace(0,2*math.pi/.32,129);basis=np.c_[np.ones(len(at)),np.sin(.32*at),np.cos(.32*at)]
 for i,p in enumerate(prior['vertices']):
  a=basis@np.asarray(p).T;assert np.max(a-upper[i])<=1e-9 and np.max(-a-upper[i+8])<=1e-9;dense+=a.size*2
 new=admit(row['packet'],row['source'],*row['wanted'],known,row['proof']['issued_at']);changed+=int(row['proof']['passed']and not new['passed'])
 zero=admit(row['packet'],row['source'],0,0,known,row['proof']['issued_at'])
 if zero['passed']and zero['terminal_cycle_qualified']:safe=zero
checks['cycle_exact_extrema']=bool(errors)and max(errors)<1e-10
checks['unsafe_original_approach_prevented']=changed>0
checks['qualified_stationary_wait_can_retain']=safe is not None and retained_allowed(safe,25.)
# Exercise exact production call-site. Previously it discarded old valid tail.
tree=ast.parse((C/'ros_bridge.py').read_text());bridge=next(n for n in ast.walk(tree)if isinstance(n,ast.ClassDef)and n.name=='Bridge');method=next(n for n in bridge.body if isinstance(n,ast.FunctionDef)and n.name=='dispatch_command');module=ast.Module(body=[ast.ClassDef(name='ActualCallsite',bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[]);ast.fix_missing_locations(module)
ns={'time':NS(monotonic=lambda:last['proof']['issued_at']),'require':require};exec(compile(module,'<production dispatch AST>','exec'),ns)
x=ns['ActualCallsite']();x.latest=last['packet'];x.motion=NS(decision_snapshot=lambda:(last['packet'],last['source']));x.planner_proxy=NS(known=known);x.retained_proof=old;x.tube_decisions=[];x.last_nominal_at=last['proof']['issued_at'];x.guard_failure=None;sent=[];x.send=lambda p:sent.append(p);x.command_sequence=0;x.commands=[]
m=NS(linear=NS(x=last['wanted'][0]),angular=NS(z=last['wanted'][1]));x.dispatch_command(m)
checks['callsite_retains_existing_valid_tail']=x.guard_failure is None and x.tube_decisions[-1]['retained_previous']and not sent
checks['anchor_and_time_not_reset']=x.retained_proof is old
x.retained_proof=dict(old,body_native_tick=old['body_native_tick']-500);x.dispatch_command(m)
checks['expired_tail_stops_at_real_callsite']=x.guard_failure is not None and sent[-1]['kind']=='stop'
checks['wait_timer_kept']="self.create_timer(.05,self.renew_wait)"in(C/'ros_bridge.py').read_text()
# Changing the public frequency must be rejected, not silently reinterpreted.
try:cycle_upper(dict(last['source']['periodic'],omega=.3))
except AssertionError:checks['frequency_change_rejected']=True
else:checks['frequency_change_rejected']=False
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,changed_saved_admissions=changed,periodic_extrema_max_error=max(errors),independent_vertex_time_checks=dense,scope='Saved original refusal, exact production handoff callsite and analytic full-phase endpoint gate. No new executed trajectory, stopping branch or recursive-safety proof.')
for n in ['ZERO_MODEL_QUALIFICATION.json','RELEASE_QUALIFICATION.json']:(O/n).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert report['passed']
