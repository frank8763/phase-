from chain_tools import *
import copy,subprocess,ast
def main():
    worker=load('v1180_zero_authority_worker',C/'worker.py');saved=sys.argv[:];sys.argv=['worker',str(C/'TASK_main.json')];negative=[]
    try:
        try:worker.main()
        except AssertionError as e:assert 'NO_NEW_MODEL_AUTHORITY'in str(e);negative.append('worker_no_authority')
        else:raise AssertionError('NO_AUTHORITY_ACCEPTED')
    finally:sys.argv=saved
    sys.path.insert(0,str(R/'experiments/v1146_causal_certificate_refresh'));from refresh import causal_packets
    p=dict(native_tick=10,sim_time=.1);s=dict(native_tick=10,time=.1,xy=[0.,0.],yaw=0.,ranges=[3.]*32)
    assert len(causal_packets([s],p)[0])==1
    for name,row in [('future_native',dict(s,native_tick=11)),('future_time',dict(s,time=.2)),('stale',dict(s,native_tick=0,time=0.))]:
        try:causal_packets([row],p)
        except AssertionError:negative.append(name)
        else:raise AssertionError('CAUSAL_NEGATIVE_ACCEPTED '+name)
    for key,val in [('historical_prefix_native',34723),('native_limit',85000),('scope','new24'),('case_id','EAST_WEST')]:
        try:task_contract(dict(read(C/'TASK_main.json'),**{key:val}))
        except AssertionError:negative.append(key)
        else:raise AssertionError('TASK_NEGATIVE_ACCEPTED '+key)
    code="from chain_tools import *\nhistory_guard(O/'not_an_actual_vehicle')\ntry:\n open(R/'runs/v858_nav2_verified/v1179/main/physics/BODY_COMMANDS.json').read()\nexcept AssertionError as e:\n assert 'FRESH_HISTORY_READ_FORBIDDEN'in str(e)\n print('HISTORY_READ_REJECTED')\nelse: raise AssertionError('OLD_HISTORY_ACCEPTED')\n"
    cp=subprocess.run([sys.executable,'-B','-c',code],cwd=C,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30);assert cp.returncode==0,cp.stdout;negative.append('old_control_history_open')
    for file in C.glob('*.py'):ast.parse(file.read_text())
    dump(O/'ENTRY_QUALIFICATION.json',dict(passed=True,negatives=negative,models=0,new_mujoco_native=0,history_guard_subprocess=cp.stdout.strip()));print('V1180_ENTRY_AND_HISTORY_GUARDS_PASS')
if __name__=='__main__':main()
