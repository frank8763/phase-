"""Separate precharged metadata, full predictive payload and original I/O caps."""
import importlib.util,json,subprocess
from pathlib import Path
from context import R,S,read,sha
META=128*1024;PAYLOAD=2*1024**2;IO=272*1024**2

def du(p):return int(subprocess.check_output(['du','-sx','-B1',str(p)],timeout=10).split()[0])if p.exists()else 0

def check(stage,extra_payload=0):
    assert stage in {'preparation','source','runtime','closed'}and type(extra_payload)is int and extra_payload>=0
    amend=read(S/'PRE_SOURCE_SCOPE_AMENDMENT.json');assert amend['maximum_predictor_constructions']==4 and amend['maximum_predictor_steps']==8830 and amend['metadata_cap_unchanged']==META and amend['payload_cap_unchanged']==PAYLOAD
    pre=read(S/'STORAGE_PRECHARGE.json');assert pre['metadata_precharge_bytes']==META and pre['predictive_payload_precharge_bytes']==PAYLOAD
    inventory=R/pre['closed_inventory_path'];assert sha(inventory)==pre['closed_inventory_sha256']
    helper=R/'experiments/v2182_fairness_mechanism_diagnosis/closed_math_reservation.py';assert sha(helper)==pre['closed_checker_sha256']
    sp=importlib.util.spec_from_file_location('v2185_exact_closed_band_recheck',helper);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);charge=m.verify_existing(read(inventory))
    other=du(R/'runs/v2182_fairness_mechanism_diagnosis')+du(R/'runs/v2183_lossless_capture_stream');assert other+charge+META<=1024**2,'METADATA_PARALLEL_PRECHARGE_CHANGED'
    mutable=du(R/'runs/v2152_weekend_research_program')+du(R/'runs/v2181_combined_close_reservation');assert mutable<=2*1024**2
    meta=sum(p.stat().st_blocks*512 for p in S.rglob('*')if p.is_file()and p.relative_to(S).parts[0]not in {'RUNTIME','SOURCE_TRANSPORT','RUNTIME_TRANSPORT'})
    assert meta+16*1024<=META,'META128KIB_REQUIRES16KIB_DIRECTORY_MARGIN'
    assert du(S/'RUNTIME')+extra_payload<=PAYLOAD,'PREDICTIVE_PAYLOAD2MIB_CAP'
    transport=du(S/'SOURCE_TRANSPORT')+du(S/'RUNTIME_TRANSPORT');assert transport<=IO
    assert du(S)+extra_payload<=META+PAYLOAD+IO
    assert pre['conservative_peak_with2MiB_payload_IO272_root512']<=16106127360 and pre['baseline_unchanged']==14873092096 and pre['new_global_credit_bytes']==0
    if stage=='runtime':
        close=read(S/'SOURCE_REMOTE_CLOSURE.json');assert close['passed']and close['all_frozen_members_actual_remote_covered']and close['exact_transport_cleanup_completed']
        assert all(not(R/n).exists()for n in close['removed_transport_paths'])
    return dict(stage=stage,meta_allocated=meta,meta_cap=META,payload_allocated=du(S/'RUNTIME'),payload_cap=PAYLOAD,transport_allocated=transport,parallel_committed=other+charge+META,mutable_parent_allocated=mutable)
