"""Equal decision work and identical physical prefix before the commit choice."""
import argparse,gzip,json
from pathlib import Path
import numpy as np
read=lambda p:json.loads(p.read_text())
lines=lambda p:[json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
def compare_pair(full,shadow):
    full,shadow=Path(full),Path(shadow);fa=lines(full/'geometry_memory/v648_execution.jsonl');sa=lines(shadow/'geometry_memory/v648_execution.jsonl')
    fc=lines(full/'geometry_memory/return_compute.jsonl');sc=lines(shadow/'geometry_memory/return_compute.jsonl');returns=[x['step'] for x in fc if x['returned']];first=min(returns) if returns else None
    keys=['qpos_full','qvel_full','ctrl','mocap_pos'];minimum=min(len(fa),len(sa));limit=minimum if first is None else first
    physical_differences=[i for i,(a,b) in enumerate(zip(fa,sa)) if any(np.max(abs(np.asarray(a[k])-np.asarray(b[k])))>1e-8 for k in keys)];first_physical=min(physical_differences) if physical_differences else None
    prefix=minimum>=limit and all(all(np.max(abs(np.asarray(a[k])-np.asarray(b[k])))<=1e-8 for k in keys) for a,b in zip(fa[:limit],sa[:limit]))
    stop=minimum-1 if first is None else first;fmap={x['step']:x for x in fc if x['step']<=stop};smap={x['step']:x for x in sc if x['step']<=stop}
    fields=['prediction_before','prediction_after','prediction_delta'];compute_equal=set(fmap)==set(smap) and all(all(fmap[s][k]==smap[s][k] for k in fields) for s in fmap)
    certificate_equal=None
    if first is not None:
        actual=full/'geometry_memory/handover_certificates'/('handover_%04d.json.gz'%first);hypothetical=shadow/'geometry_memory/shadow_handover_certificates'/('shadow_%04d.json.gz'%first)
        if actual.exists() and hypothetical.exists():
            with gzip.open(actual,'rt') as stream:a=json.load(stream)
            with gzip.open(hypothetical,'rt') as stream:b=json.load(stream)
            fields=['qpos','qvel','controls','prefix_poses','prefix_command','initial_qpos','initial_qvel','target','forecast_state','minimum_causal_predicted_clearance_m','minimum_predicted_self_domain_margin_m','terminal_speed_m_s','real_entry_qpos','real_entry_qvel','real_entry_time','old_created_step','old_native_cursor','metadata']
            certificate_equal=all(a[k]==b[k] for k in fields)
        else:certificate_equal=False
    ar=read(full/'geometry_memory/result.json');br=read(shadow/'geometry_memory/result.json')
    checks={'registered_modes':read(full/'ABLATION_PROTOCOL.json')['mode']=='FULL' and read(shadow/'ABLATION_PROTOCOL.json')['mode']=='SHADOW_COMPLETE_TAIL','same_task_phase':ar['seed']==br['seed'] and ar['course_phase']==br['course_phase'],'same_model_and_initial':ar['normalized_initial_state_hash']==br['normalized_initial_state_hash'] and read(full/'STATIC_PROTOCOL.json')['full_model_sha256']==read(shadow/'STATIC_PROTOCOL.json')['full_model_sha256'],'identical_physical_prefix':bool(prefix),'equal_prediction_work_on_common_decisions':bool(compute_equal),'same_first_proposed_full_certificate':first is None or certificate_equal is True,'physical_divergence_not_before_commit_choice':first_physical is None or(first is not None and first_physical>=first)}
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'mechanism_triggered':first is not None,'first_full_commit_step':first,'first_physical_difference_step':first_physical,'same_first_candidate_certificate':certificate_equal,'matched_return_decisions':len(fmap),'common_prefix_prediction_steps':None if not fmap else fmap[max(fmap)]['prediction_after'],'full_arrival':ar['strict_safe_arrival'],'shadow_arrival':br['strict_safe_arrival'],'full_public_steps':ar['public_steps'],'shadow_public_steps':br['public_steps'],'full_private_integrations':ar['prediction_steps'],'shadow_private_integrations':br['prediction_steps'],'verification_integrations':0,'scope':'Equal work on matching pre-commit decisions only; divergent total work and unequal endpoints must be reported separately.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('full');p.add_argument('shadow');p.add_argument('--output',required=True);args=p.parse_args();result=compare_pair(args.full,args.shadow)
    with Path(args.output).open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));assert result['status']=='PASS'
