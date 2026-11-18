"""Authorization/deadline and main->audit->repeat supervision without models."""
from response_tools import *
import ast
import copy
import tempfile
import numpy as np
start=load('v1157_start_contract',C/'start.py')


def main():
    assert not (O/'LAUNCH_QUALIFICATION.json').exists()
    auth=dict(authorized=True,version='V1157',scope='fixed_response_main_and_complete_repeat',
              window_seconds=5400,user_instruction='SYNTHETIC_QUALIFICATION_ONLY')
    assert start.validate_authorization(auth)==5400
    rejected=[]
    for key,value in [('authorized',False),('version','old'),('scope','dynamic24'),('window_seconds',7200),('window_seconds',5400.),('user_instruction','')]:
        try:start.validate_authorization(dict(auth,**{key:value}))
        except AssertionError:rejected.append(key)
        else:raise AssertionError('AUTHORIZATION_NEGATIVE_ACCEPTED '+key)
    w=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
           absolute_deadline_unix=time.time()+10,hard_stop_monotonic=time.monotonic()+10)
    assert 0<remaining(w)<=10
    assert remaining(dict(w,hard_stop_monotonic=time.monotonic()-1))<0
    assert remaining(dict(w,absolute_deadline_unix=time.time()-1))<0
    try:remaining(dict(w,boot_id='wrong'))
    except AssertionError:rejected.append('boot_changed')
    else:raise AssertionError('BOOT_NEGATIVE_ACCEPTED')
    supervisor=[]
    for scenario in ['first_failure','success_pair']:
        m=load('v1157_supervisor_'+scenario,C/'campaign.py')
        with tempfile.TemporaryDirectory(dir=O,prefix='supervision_only_')as folder:
            root=Path(folder);local_c=root/'experiments/v1157_response_execution';local_c.mkdir(parents=True)
            local_o=root/'runs/v1157_response_execution';local_o.mkdir(parents=True)
            (root/'docs').mkdir();(root/'REVIEW_PENDING').write_bytes((R/'REVIEW_PENDING').read_bytes())
            dump(root/'CURRENT_EXPERIMENT.json',dict(status='SYNTHETIC_QUALIFICATION_ONLY',active_run=None))
            (root/'RESEARCH_STATUS.md').write_text('synthetic supervisor only\n')
            (local_o/'GUARD.bin').write_bytes((R/'REVIEW_PENDING').read_bytes())
            for p in ['APPROVAL.json','QUALIFICATION.json','ISOLATED_QUALIFICATION.json','LAUNCH_QUALIFICATION.json']:
                dump(local_o/p,dict(models_authorized=True,passed=True,synthetic=True))
            dump(local_o/'ROUND_WINDOW.json',dict(absolute_deadline_unix=time.time()+3600))
            tasks=[]
            for role in ['main','repeat']:
                task=dict(task_id=role,output=str(root/'runs/v858_nav2_verified/v1157'/role),synthetic=True)
                tasks.append(task);dump(local_c/('TASK_'+role+'.json'),task)
            dump(local_c/'TASKS.json',tasks)
            if scenario=='first_failure':worker_code='import sys\nsys.exit(23)\n'
            else:
                worker_code='''import sys,json,gzip\nfrom pathlib import Path\nimport numpy as np\nt=json.loads(Path(sys.argv[1]).read_text());o=Path(t['output']);p=o/'physics';p.mkdir(parents=True)\nr=dict(passed=True,synthetic=True,models=0,new_actual_native=0,own_replay_native=0,analytical_cpp_native=0,analytical_python_native=0,capture_native=261)\n(o/'RESULT.json').write_text(json.dumps(r))\nnp.savez_compressed(p/'NATIVE_TRACE.npz',qpos=np.zeros((1,2)),qvel=np.zeros((1,2)),ctrl=np.zeros((1,4)),mocap_pos=np.empty((1,0,3)),mocap_quat=np.empty((1,0,4)),time=np.array([.01]))\nnp.savez_compressed(p/'INITIAL_STATE.npz',state=np.zeros(2))\n(p/'scene_model.mjb').write_bytes(b'SYNTHETIC_NOT_A_MODEL')\nfor name in ['CONTACTS.json.gz','SENSORS.json.gz']:\n with gzip.open(p/name,'wt')as f:json.dump([],f)\n'''
            (local_c/'worker.py').write_text(worker_code)
            (local_c/'audit.py').write_text("import sys,json\nfrom pathlib import Path\nt=json.loads(Path(sys.argv[1]).read_text());(Path(t['output'])/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(dict(passed=True,synthetic=True,analytical_cpp_native=0,analytical_python_native=0)))\n")
            # This shell runs ONLY the temporary synthetic scripts. No physical
            # factory or actual run_phase is invoked in this supervision test.
            shim=root/'run_phase.sh';shim.write_text('#!/bin/sh\nexec '+sys.executable+' -B "$@"\n');shim.chmod(0o755)
            m.R=root;m.C=local_c;m.O=local_o;m.source_ok=lambda:True;m.used=lambda:0;m.remaining=lambda:3600.
            m.main()
            done=read(local_o/'COMPLETION.json')
            assert sha(root/'REVIEW_PENDING')==GUARD_SHA
            assert read(local_o/'APPROVAL.json')['models_authorized']is False
            if scenario=='first_failure':
                assert not done['passed'] and done['unexecuted']==['repeat'] and len(done['stages'])==1
                assert done['physical_counts']['new_actual_native']is None
            else:
                assert done['passed'] and done['complete_repeat']['passed'] and len(done['stages'])==2
                assert all(r['audit']['passed']for r in done['stages'])
            supervisor.append(dict(scenario=scenario,passed=True,stages=[r['stage']for r in done['stages']],
                synthetic_only=True,actual_models=0,actual_physical_native=0))
    for file in C.glob('*.py'):ast.parse(file.read_text())
    proof=dict(passed=True,authorization_negatives=rejected,wall_monotonic_and_boot_checked=True,
               supervision=supervisor,guard_original=sha(R/'REVIEW_PENDING')==GUARD_SHA,
               models=0,physical_native=0,analytical_native=0,new_window_opened=False)
    dump(O/'LAUNCH_QUALIFICATION.json',proof);print(encode(proof))


if __name__=='__main__':main()
