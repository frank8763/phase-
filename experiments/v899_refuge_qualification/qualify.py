"""Saved actual cause states, truthful breadcrumbs and admission/performance checks."""
import ast,gzip,json,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v899_refuge_qualification'
sys.path.insert(0,str(R/'experiments/v897_refuge_navigation'))
from refuge_logic import choose_refuge,wait_ok,exit_path_ok
def main():
    p=O/'inputs'
    with np.load(p/'physics__NATIVE_TRACE.npz')as compressed:z={k:compressed[k]for k in ['time','qpos']}
    journal=json.loads(gzip.decompress((p/'MOTION_ENVELOPE.json.gz').read_bytes()));known=json.loads((p/'physics__SETUP.json').read_text())['known'];cases=[];times=[];fixtures=[]
    for target in [70.,90.,100.,110.,120.,126.]:
        i=int(np.argmin(abs(z['time']-target)));q=z['qpos'][i];yaw=2*math.atan2(q[6],q[3]);body=[*q[:2],yaw];state=next(x for x in reversed(journal['states'])if x['time']<=float(z['time'][i]));age=float(z['time'][i])-state['time'];history=[]
        for j in range(0,i+1,10):
            qj=z['qpos'][j];yj=2*math.atan2(qj[6],qj[3]);b=[*qj[:2],yj]
            if not history or np.linalg.norm(qj[:2]-np.asarray(history[-1]['body'][:2]))>=.05:history.append(dict(native_tick=j+1,sim_time=float(z['time'][j]),body=b))
        t=time.perf_counter();choice=choose_refuge(body,history,state['support_bounds'],age,known);times.append(time.perf_counter()-t)
        cases.append(dict(at=target,wait_ok=wait_ok(body,state['support_bounds'],age),choice=choice,selection_wall_s=times[-1]))
        if choice is not None:fixtures.append(dict(body=body,state=state,age=age,choice=choice))
    # Synthetic true-world-free geometry checks at the real function seam.
    far=np.max(np.asarray([[3.,3.]])@__import__('refuge_logic').NORMALS.T,axis=0)
    checks=dict(saved_admitted_refuge_exists=bool(fixtures),original_failed_stop_hold_is_rejected=not cases[-1]['wait_ok'],empty_history_refuge_rejected=choose_refuge([0.,0.,0.],[],far,0.,known)is None,unseen_not_a_tracked_certificate=wait_ok([0.,0.,0.],None,0.),selection_under50ms=max(times)<.05,all_selected_paths_and_holds_qualified=all(x['choice']is None or x['choice']['geometry_contract']['passed']for x in cases),platform1200_response_gate=json.loads((R/'runs/v896_overnight_20261108/platform_continuation_result.json').read_text())['passed'])
    # Exact production entries must reject before importing a vehicle or ROS.
    import subprocess
    for name in ['native_worker.py','ros_worker.py','preflight_worker.py']:
        code="""import runpy,sys,importlib.abc,json
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0]in ['mujoco','rclpy','vehicle','physical']:raise AssertionError('FORBIDDEN_IMPORT '+fullname)
sys.meta_path.insert(0,Block());d=runpy.run_path(sys.argv[1],run_name='zero');t=json.loads((d['C']/'TASKS.json').read_text())[0]
try:(d['engine'].run if 'engine'in d else d['run'])(t,{},'FAKE')
except RuntimeError as e:assert str(e)=='MODELS_NOT_AUTHORIZED',str(e)
else:raise AssertionError('ENTRY_ALLOWED')
"""
        a=subprocess.run([sys.executable,'-B','-c',code,str(R/'experiments/v897_refuge_navigation'/name)],cwd=R,capture_output=True,text=True,timeout=10);checks[name+'_unauthorized_before_models']=a.returncode==0
        if a.returncode:(O/(name+'.zero_error')).write_text(a.stdout+a.stderr)
    for f in(R/'experiments/v897_refuge_navigation').glob('*.py'):ast.parse(f.read_text(),filename=str(f))
    result=dict(passed=all(checks.values()),checks=checks,cases=cases,selection_max_wall_s=max(times),models=0,integrations=0,not_a_recursive_safety_proof=True)
    (O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');(O/'REFUGE_FIXTURES.json').write_text(json.dumps(fixtures,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
