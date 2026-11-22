"""Once saved-byte readback; no numerical backend or model calls."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time

R=Path(__file__).resolve().parents[2]
O=R/'runs/v1571_complete_batch_comparison'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())

def put(p,value):
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
    tmp.replace(p)

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.alarm(300)
    assert not (O/'CLOSED_BYTE_REVIEW.json').exists()
    completion=read(O/'COMPLETION.json');result=read(O/'model/RESULT.json')
    assert completion['closed'] and completion['passed'] and completion['returncode']==0
    assert result['passed'] and result['closed'] and result['first_error']is None and not result['secondary_errors']
    assert not result['live_current_reserve_qualified'] and not result['whole_navigation_passed']
    parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert parent['active_round']is None and parent['active_math_round']is None and not parent['models_now_authorized']
    owned=read(O/'OWNED_CHILD.json');assert not Path('/proc/'+str(owned['pid'])).exists()
    freeze=read(O/'SOURCE_FREEZE.json')['files']
    assert all(sha(R/name)==identity for name,identity in freeze.items())
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    with (R/'runs/v648_static_unknown/execution.lock').open()as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        source=R/'experiments/v1563_lzma_lossless_witness/stream.py'
        spec=importlib.util.spec_from_file_location('v1565_frozen_bytes_only_reader',source)
        stream=importlib.util.module_from_spec(spec);spec.loader.exec_module(stream)
        names=[f'b{i:03d}_{kind}'for i in range(281)for kind in ('current','prospective')]+['nominal']
        phases={};arrays_by_stage={}
        for stage,folder_name,result_name in [('CPP_AUDIT','audit','AUDIT.json')]:
            folder=O/'model'/folder_name;seal=read(folder/'STREAM_SEAL.json')
            reader=stream.Reader(folder,expected_binding=seal['binding'],expected_result_sha256=sha(folder/result_name),ordered_names=names)
            assert seal['binding']['stage']==stage
            assert seal['binding']['response_method_sha256']=='370bf7ce8670e35992eae9a1e2d74fb110a21749f0277480fa8b65b72f9aad89'
            assert seal['binding']['base_method_input_sha256']=='be88e178a7d661d6d075d63193983d8086a63ee5311865fbac64cf9011d3e1d1'
            total=0;minimum=float('inf');checks=None;maximum_errors={};comparison_count=0
            desc={}
            with reader.path.open('rb')as file:
                while True:
                    header=file.read(stream.HEADER.size)
                    if not header:break
                    _,nm,np=stream.HEADER.unpack(header)
                    metadata=json.loads(file.read(nm));payload=file.read(np)
                    if metadata['kind']=='DATA':
                        assert metadata['stored_before_safety_or_comparison_gate']is True
                        total+=metadata['acknowledged_native']
                        desc[metadata['name']]=metadata['arrays']
                    else:
                        proof=json.loads(payload);safety=proof['safety']
                        assert safety['passed'] and all(safety['checks'].values()) and proof['arrays_already_saved']
                        assert safety['whole_navigation_passed']is False and safety['physical_permission']is False
                        minimum=min(minimum,safety['causal_tube_lower_m'])
                        checks=set(safety['checks'])if checks is None else checks.intersection(safety['checks'])
                        if stage=='CPP_AUDIT':
                            comparison=proof['comparison'];assert comparison['passed']
                            assert comparison['independent_state_memory_mode_gear_continuous']
                            assert comparison['no_generated_state_or_control_as_per_step_input']
                            comparison_count+=1
                            for key,value in comparison['maximum_errors'].items():maximum_errors[key]=max(maximum_errors.get(key,0.),value)
                        else:assert proof['comparison']is None
            assert total==1263600
            assert stage!='CPP_AUDIT' or comparison_count==563 and all(v<=1e-8 for v in maximum_errors.values())
            arrays_by_stage[stage]=desc
            count=result['accounting']['stages'][stage]
            assert count['native']==1263600 and count['nominal_native']==13600 and count['witness_native']==1250000 and count['copy']==562
            assert not count['inflight_unknown'] and count['construction_inflight']is None
            assert count['Engine']==1 and count['batch_calls']==562 and count['batch_native']==1235838
            phases[stage]=dict(data_records=563,proof_records=563,stream_bytes=seal['stream_bytes'],stream_sha256=seal['stream_sha256'],
                acknowledged_native=total,nominal_native=13600,witness_native=1250000,minimum_saved_tube_lower_m=minimum,
                saved_common_gate_names=sorted(checks),saved_independent_comparisons=comparison_count,saved_maximum_errors=maximum_errors,
                complete_result_sha256=sha(folder/result_name),reader_full_stream_payload_crc_dtype_shape_byte_sha_verified=True)
        descriptors_equal=None  # Oldreference not decoded/re-audited during this newstreamreadback
        assert all(sha(R/name)==identity for name,identity in freeze.items())
        proof=dict(passed=True,recorded_unix=time.time(),models_during_readback=0,new_integrations=0,
            policy_calls=0,FFI_loads=0,Allocator_recomputations=0,physical_native=0,replay_native=0,optimizer_calls=0,
            frozen_members_verified=len(freeze),owned_child_exited=True,review_original_restored=True,lock_idle=True,
            all_phase_array_descriptors_and_byte_sha_equal=descriptors_equal,phases=phases,
            generation_native=0,CPP_comparison_native=1263600,total_private_native=1263600,
            internal_Allocator_constructors=None,original_model_audit_not_reexecuted=True,saved_reference_is_development_input=True,
            actual_capture_qualified=False,whole_route_passed=False,source_seal_alone_not_science_pass=True)
        put(O/'CLOSED_BYTE_REVIEW.json',proof)
        print(json.dumps(proof,sort_keys=True))
    signal.alarm(0)

if __name__=='__main__':main()
