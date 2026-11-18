"""Bounded four-process saved-state ablation, final paired result table."""
import concurrent.futures,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def main():
    assert not(O/'RUN_CLAIM.json').exists(),'ONE_FIXED_STUDY'
    assert json.loads((O/'RESTORE_CHUNKS_COMPLETE.json').read_text())['passed']
    assert(R/'REVIEW_PENDING').exists();guard=(R/'REVIEW_PENDING').read_bytes();start=time.monotonic()
    files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [*C.glob('*.py'),C/'PROTOCOL.md']}
    dump(C/'SOURCE_FREEZE.json',dict(files=files,models=0,slots=list(range(17,25)),delays_native=list(range(0,2000,50)),completed_job_reuse=[17,22,24],restored_input_provenance='all32 input memberSHA bind to original V1281 GitHub inventory'))
    dump(O/'RUN_CLAIM.json',dict(started_unix=time.time(),software_deadline_monotonic=start+1500,physical_models=0,cpus=[2,3,4,5]))
    def run(slot):
        prior = O / ('RESULT_slot17.json' if slot == 17 else f'RESULT_RELAY_slot{slot:02}.json')
        if slot in [17,22,24]:
            result=json.loads(prior.read_text());assert result['passed'];return dict(result,reused_unchanged_completed_study_job=True)
        cpu=2+(slot-17)%4;env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='')
        with(O/f'slot{slot:02}.console').open('x')as log:
            p=subprocess.run(['/home/linghu/miniconda3/envs/mk_mujoco/bin/python','-B',str(C/'worker_final.py'),str(slot),str(cpu)],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=650)
        record=json.loads((O/f'RESULT_FINAL_slot{slot:02}.json').read_text());return record
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        futures=[pool.submit(run,slot)for slot in range(17,25)]
        for future in futures:
            try:r=future.result()
            except BaseException as exc:r=dict(passed=False,error=repr(exc),slot=None)
            results.append(r);dump(O/'PARTIAL_RESULTS.json',results)
            print(json.dumps(dict(complete=len(results),total=8,slot=r.get('slot'),passed=r['passed'])),flush=True)
    passed=len(results)==8 and all(x['passed']for x in results)
    success=[x for x in results if x['passed']]
    summary=dict(passed=passed,closed=True,slots_expected=8,slots_completed=len(results),valid_source_reconstructions=len(success),
                 original_nominal_gate_passed=sum(t['original_full_gate'] for x in success for t in x['trials']),
                 complete_reserved_gate_passed=sum(t['complete_admission_passed'] for x in success for t in x['trials']),
                 secondary_reserve_ablation_exploratory=True,
                 full_selected_admission=sum(bool(x['selected']['complete_admission_passed'])for x in success),
                 without_wait_admission=sum(bool(x['without_wait']['complete_admission_passed'])for x in success),
                 timing_window_candidates_per_slot=40,total_timing_trials=sum(len(x['trials'])for x in success),
                 same_states_controls_memory_max_error=max((x['selected_reference_error']for x in success),default=None),
                 analytical_cpp_native=sum(x['analytical_cpp_native']for x in results if isinstance(x.get('analytical_cpp_native'),int)),
                 analytical_cpp_partial_unknown=any(x.get('analytical_cpp_native')is None for x in results),
                 wall_s=time.monotonic()-start,per_job_cpu_s=[dict(slot=x.get('slot'),cpu_s=x.get('cpu_s'),wall_s=x.get('wall_s'))for x in results],
                 guard_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,
                 source_unchanged=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in files.items()),
                 models=0,physical_native=0,training_updates=0,stage_access=False,
                 scope='saved-state temporal mechanism admission, not full navigation, independent statistical replication, or unexposed generalization')
    dump(O/'COMPLETION.json',summary);print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
