"""New campaign first-failure/full-pair control flow; synthetic subprocesses."""
from chain_tools import *
import tempfile
WORKER='''import sys,json,gzip\nfrom pathlib import Path\nimport numpy as np\nt=json.loads(Path(sys.argv[1]).read_text());o=Path(t['output']);p=o/'physics';p.mkdir(parents=True)\nr=dict(passed=True,synthetic=True,error=None,evidence_saved=True,replay=dict(passed=True),models=0,new_actual_native=0,own_replay_native=0,analytical_cpp_native=0,analytical_python_native=0)\n(o/'RESULT.json').write_text(json.dumps(r))\nnp.savez_compressed(p/'NATIVE_TRACE.npz',qpos=np.zeros((1,2)),qvel=np.zeros((1,2)),ctrl=np.zeros((1,4)),mocap_pos=np.empty((1,0,3)),mocap_quat=np.empty((1,0,4)),time=np.array([.01]))\nnp.savez_compressed(p/'INITIAL_STATE.npz',state=np.zeros(2))\n(p/'scene_model.mjb').write_bytes(b'SYNTHETIC_NOT_A_MODEL')\nfor file in ['CONTACTS.json.gz','SENSORS.json.gz']:\n with gzip.open(p/file,'wt')as f:json.dump([],f)\n'''
def main():
    proofs=[]
    for scenario in ['first_failure','main_and_complete_repeat']:
        m=load('v1180_supervision_'+scenario,C/'campaign.py')
        with tempfile.TemporaryDirectory(dir=O,prefix='synthetic_supervision_')as folder:
            root=Path(folder);c=root/'experiments/v1180_gap_response_execution';o=root/'runs/v1180_gap_response_execution';c.mkdir(parents=True);o.mkdir(parents=True)
            (root/'REVIEW_PENDING').write_bytes((R/'REVIEW_PENDING').read_bytes());(o/'GUARD.bin').write_bytes((R/'REVIEW_PENDING').read_bytes())
            tasks=[]
            for t in read(C/'TASKS.json'):
                t=dict(t,output=str(root/'runs/v858_nav2_verified/v1180'/t['task_id']),synthetic=True);tasks.append(t);dump(c/('TASK_'+t['task_id']+'.json'),t)
            dump(c/'TASKS.json',tasks);dump(o/'APPROVAL.json',dict(models_authorized=True));dump(o/'ROUND_WINDOW.json',dict(absolute_deadline_unix=time.time()+10000))
            for n in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json','LAUNCH_QUALIFICATION.json','SUPERVISOR_QUALIFICATION.json','ENTRY_QUALIFICATION.json','AUDIT_QUALIFICATION.json']:dump(o/n,dict(passed=True,synthetic=True))
            if scenario=='first_failure':script="import sys,json\nfrom pathlib import Path\nt=json.loads(Path(sys.argv[1]).read_text());o=Path(t['output']);o.mkdir(parents=True);(o/'RESULT.json').write_text(json.dumps(dict(passed=False,error=None,evidence_saved=False,models=0,new_actual_native=0,own_replay_native=0,analytical_cpp_native=0,analytical_python_native=0)));sys.exit(23)\n"
            else:script=WORKER
            (c/'worker.py').write_text(script);(c/'audit.py').write_text("import sys,json\nfrom pathlib import Path\nt=json.loads(Path(sys.argv[1]).read_text());(Path(t['output'])/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(dict(passed=True,synthetic=True,analytical_cpp_native=0)))\n")
            (c/'finish.py').write_text("from pathlib import Path\nPath(__file__).resolve().parents[2].joinpath('FINISHED_ZERO_MODEL').write_text('synthetic')\n")
            shim=root/'run_phase.sh';shim.write_text('#!/bin/sh\nexec '+sys.executable+' -B "$@"\n');shim.chmod(0o755)
            m.R=root;m.C=c;m.O=o;m.source_ok=lambda:True;m.remaining=lambda:10000.;m.main()
            d=read(o/'COMPLETION.json');assert sha(root/'REVIEW_PENDING')==GUARD and not read(o/'APPROVAL.json')['models_authorized']and(root/'FINISHED_ZERO_MODEL').exists()
            if scenario=='first_failure':assert not d['passed']and len(d['stages'])==1 and len(d['unexecuted'])==1
            else:assert d['passed']and len(d['stages'])==2 and d['complete_repeat']['passed']
            proofs.append(dict(scenario=scenario,passed=True,stages=[r['stage']for r in d['stages']],physical_models=0))
    dump(O/'SUPERVISOR_QUALIFICATION.json',dict(passed=True,scenarios=proofs,models=0,physical_native=0,new_state_prediction=0));print('SYNTHETIC_SUPERVISION_PASS')
if __name__=='__main__':main()
