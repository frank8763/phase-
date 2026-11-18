"""Call the original independent time-selection verifier, not the new worker."""
import importlib.abc
import sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_INDEPENDENT_AUDIT '+name)
sys.meta_path.insert(0,NoModels())
import concurrent.futures,importlib.util,json,os,subprocess,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;P=R/'runs/v1299_paired_mechanism_study'


def single(slot):
    cpu=2+(slot-17)%4;os.sched_setaffinity(0,{2,cpu});start=time.monotonic();proof=dict(slot=slot,passed=False,models=0,physical_native=0)
    try:
        source=R/'experiments/v1270_ew_causal_time_windows';sys.path.insert(0,str(source))
        import audit_time
        os.sched_setaffinity(0,{cpu})
        candidates=[P/f'input_slot{slot:02}',P/f'input_chunks_slot{slot:02}'];folder=next(p for p in candidates if(p/'RESTORED.json').exists()and json.loads((p/'RESTORED.json').read_text()).get('passed'))
        x=json.loads((folder/'EW_ONWARD_INPUT.json').read_text());selected=json.loads((folder/'EW_ONWARD_SELECTION.json').read_text())
        with audit_time.np.load(folder/'EW_ONWARD_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
        result=audit_time.verify(x,table,selected);assert result['passed']
        record=P/('RESULT_slot17.json'if slot==17 else f'RESULT_RELAY_slot{slot:02}.json'if slot in[22,24]else f'RESULT_FINAL_slot{slot:02}.json');study=json.loads(record.read_text())
        if 'complete_time_windows'in result:assert result['passing_windows']==len(study['passing_windows']) and result['selected_wait_native']==study['selected_wait_native']
        proof.update(passed=True,original_independent_verifier=result,original_source_required_raw_m=float(audit_time.q.REQUIRED),new_study_table_matches_original_counts=True,cpu=cpu)
    except BaseException as exc:proof.update(error=repr(exc),traceback=traceback.format_exc())
    proof['wall_s']=time.monotonic()-start;(O/f'TIME_AUDIT_slot{slot:02}.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:proof.get(k)for k in ['slot','passed','error','wall_s']}),flush=True);return proof


def main():
    assert json.loads((P/'COMPLETION.json').read_text())['passed'];O.mkdir(exist_ok=True);assert not(O/'FINAL_TIME_AUDIT.json').exists()
    def run(slot):
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='')
        with(O/f'audit_slot{slot:02}.console').open('x')as stream:
            p=subprocess.run(['/home/linghu/miniconda3/envs/mk_mujoco/bin/python','-B',str(Path(__file__).resolve()),'--slot',str(slot)],cwd=R,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=300)
        assert p.returncode==0,'INDEPENDENT_AUDIT_PROCESS_FAILED'
        return json.loads((O/f'TIME_AUDIT_slot{slot:02}.json').read_text())
    start=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:results=list(pool.map(run,range(17,25)))
    proof=dict(passed=all(r['passed']for r in results),results=results,wall_s=time.monotonic()-start,analytical_cpp_native=sum(r.get('original_independent_verifier',{}).get('analytical_cpp_native',0)for r in results),models=0,physical_native=0)
    (O/'FINAL_TIME_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)


if __name__=='__main__':
    if len(sys.argv)>1:raise SystemExit(0 if single(int(sys.argv[2]))['passed']else 1)
    main()
