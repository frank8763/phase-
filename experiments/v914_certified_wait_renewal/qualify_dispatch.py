"""Execute exact production Bridge callback methods without ROS or vehicle models."""
import ast,json,sys
from pathlib import Path
from types import SimpleNamespace as NS
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v914_certified_wait_renewal';sys.path.insert(0,str(C))
tree=ast.parse((C/'ros_bridge.py').read_text());bridge=next(n for n in ast.walk(tree)if isinstance(n,ast.ClassDef)and n.name=='Bridge')
methods=[n for n in bridge.body if isinstance(n,ast.FunctionDef)and n.name in ['command','renew_wait']]
clock=[100.]
class Twist:
 def __init__(self):self.linear=NS(x=0.);self.angular=NS(z=0.)
ns={'time':NS(monotonic=lambda:clock[0]),'Twist':Twist};module=ast.Module(body=[ast.ClassDef(name='ProductionMethods',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[]);ast.fix_missing_locations(module);exec(compile(module,'<exact production method AST>','exec'),ns)
x=ns['ProductionMethods']();x.guard_failure=None;x.latest=dict(phase='WAITING');x.last_nominal_at=None;calls=[];x.dispatch_command=lambda m,renewal=False:calls.append((m.linear.x,m.angular.z,renewal,x.last_nominal_at))
x.renew_wait();checks=dict(prearm_no_command=not calls)
x.latest['phase']='RUNNING';m=Twist();m.linear.x=.1;x.command(m);checks['fresh_nominal_preserved']=calls[-1]==(.1,0.,False,100.)
clock[0]=100.14;x.renew_wait();checks['no_premature_override']=len(calls)==1
clock[0]=100.151;x.renew_wait();checks['stale_moving_intent_becomes_zero']=calls[-1]==(0.,0.,True,100.)
clock[0]=105.;x.renew_wait();checks['long_wait_still_zero']=calls[-1][:3]==(0.,0.,True)
x.guard_failure='STOP';before=len(calls);x.renew_wait();checks['guard_failure_never_renews']=len(calls)==before
checks['actual_timer_installed']="self.create_timer(.05,self.renew_wait)"in(C/'ros_bridge.py').read_text()
saved=json.loads((O/'SAVED_WAIT_QUALIFICATION.json').read_text());checks['actual_failed_waiting_prefix']=saved['passed']
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,exact_production_callback_AST=True)
for n in ['ZERO_MODEL_QUALIFICATION.json','RELEASE_QUALIFICATION.json']:(O/n).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report));assert report['passed']
