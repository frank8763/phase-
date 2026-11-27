"""Static/precharge-only preparation; no numeric import or Source claim."""
import ast,datetime,fcntl,importlib.util,json,os,subprocess,sys
from pathlib import Path
from context import R,C,S,PARENT,read,sha,files
from fixture import fixed,RECEIPT,SETUP,EVIDENCE,RESULT,CLOSURE
META=128*1024;PAYLOAD=2*1024**2

def main():
    assert os.sched_getaffinity(0)=={5}and not S.exists()
    locks=[]
    for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
        f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    inventory=R/'runs/v2152_weekend_research_program/CLOSED_V2184_PREPARATION_BAND.json';mod=R/'experiments/v2182_fairness_mechanism_diagnosis/closed_math_reservation.py'
    spec=importlib.util.spec_from_file_location('v2185_conditional_closed_band_check',mod);closed=importlib.util.module_from_spec(spec);spec.loader.exec_module(closed);charge=closed.verify_existing(read(inventory));assert charge==192*1024
    du=lambda p:int(subprocess.check_output(['du','-sx','-B1',str(p)],timeout=10).split()[0])
    other=du(R/'runs/v2182_fairness_mechanism_diagnosis')+du(R/'runs/v2183_lossless_capture_stream');assert other+charge+META<=1024**2
    mutable=du(inventory.parent)+du(R/'runs/v2181_combined_close_reservation');assert mutable<=2*1024**2
    capacity=R/'runs/v2181_combined_close_reservation/CAPACITY_CANDIDATE.json';budget=read(capacity);assert budget['frozen_prior_baseline_bytes']==14873092096 and budget['all_prior_evidence_upper_bytes']==15231647744
    peak=budget['all_prior_evidence_upper_bytes']+budget['preparation_bytes']+budget['metadata_bytes']+PAYLOAD+(272+512)*1024**2;assert peak<=16106127360
    # Verify exact public input/old raw outputs with stdlib, not a model query.
    parent=files(PARENT/'SOURCE_FREEZE.json');source=dict(parent)
    for n in [RECEIPT,SETUP,EVIDENCE,RESULT,CLOSURE]:source[n]=sha(R/n)
    fixture=fixed(source);assert len(fixture['cases'])==2 and fixture['world_truth_not_supplied']
    # Static source shape witnesses, never import the model or response here.
    model=R/'experiments/v1003_causal_recovery_execution/predictor.py';tree=ast.parse(model.read_text());assert 'self.state.shape == (8,)'in ast.unparse(tree)
    response=R/'experiments/v1922_dwa_five_admission_checked/response.py';rt=ast.unparse(ast.parse(response.read_text()));assert 'len(ss), 5'in rt and "predictor.adapter.last"in rt and '2200'in rt
    raw=2*(2206*8+2205*4+2206*5+2205*3)*8;assert raw==705808 and raw+8192<PAYLOAD
    for p in C.glob('*.py'):ast.parse(p.read_text())
    p=subprocess.run(['/usr/bin/python3','-B',str(C/'entry.py')],cwd=R,capture_output=True,timeout=10);assert p.returncode==77 and json.loads(p.stdout)['refused_before_numerical_import']and not p.stderr
    pre=dict(scope='V2185_PREPARATION_ONLY_NO_SOURCE_OR_MODEL_AUTHORITY',created_at=datetime.datetime.now().astimezone().isoformat(),metadata_precharge_bytes=META,predictive_payload_precharge_bytes=PAYLOAD,payload_from_original_task224MiB_not_metadata=True,original_task_cap_bytes=224*1024**2,original_IO_cap_bytes=272*1024**2,original_root_cap_bytes=512*1024**2,metadata_source_archive_readback_not_yet_sized=True,closed_inventory_path=str(inventory.relative_to(R)),closed_inventory_sha256=sha(inventory),closed_checker_sha256=sha(mod),closed_charge_bytes=charge,other_parallel_allocated_bytes=other,parallel_peak_with_new_metadata=other+charge+META,parallel_cap=1024**2,capacity_path=str(capacity.relative_to(R)),capacity_sha256=sha(capacity),baseline_unchanged=14873092096,all_prior_evidence_upper_unchanged=15231647744,new_global_credit_bytes=0,conservative_peak_with2MiB_payload_IO272_root512=peak,global_limit=16106127360,mutable_parent_allocated=mutable,typed_raw_array_bytes=raw,proposed_two_NPZ_header_upper=8192,typed_shape_source_witnesses={str(model.relative_to(R)):sha(model),str(response.relative_to(R)):sha(response)},unadmitted_entry_refusal=77,original_input_and_raw_output_files_SHA256={n:source[n]for n in [RECEIPT,SETUP,EVIDENCE,RESULT,CLOSURE]},Source_or_predictor_imports_constructors_steps_models_physics=0,preparation_first_failure='Before creating S2185, fixed() rejected the four original public map provenance fields(source/source_sha256/bootstrap_seed/scope). Exact six-field whitelist now preserves them; no geometry/input/model/parameter changed.',remaining=['owner','exact stored NPZ header bound','full source readiness and qualification','all remote source recovery','one admitted numeric run','exact runtime recovery'])
    S.mkdir();(S/'STORAGE_PRECHARGE.json').write_text(json.dumps(pre,indent=2)+'\n')
    assert du(S)<=META
    print(json.dumps(dict(preparation=True,new_metadata_precharge=META,separate_predictive_payload_precharge=PAYLOAD,global_peak=peak,parallel_peak=pre['parallel_peak_with_new_metadata'],Source_or_model_calls=0)))
if __name__=='__main__':main()
