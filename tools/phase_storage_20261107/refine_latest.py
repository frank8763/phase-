"""Keep actual latest trajectory and terminal failure witnesses; prune unselected pools."""
import collections,gzip,json
from pathlib import Path
from plan import R,OUT,dump

def main():
    assert not(OUT/'ASSET_REMOTE_VERIFICATION.json').exists()
    plan=json.loads((OUT/'PLAN.json').read_text());g=R/'runs/v855_renewal_worker/v855_RENEW64_328_main_slot01/paired/geometry_memory';rows=[json.loads(x)for x in(g/'control_decisions.jsonl').read_text().splitlines()];step=max(x['step']for x in rows);witnesses=set()
    for row in rows:
        if row['step']!=step:continue
        for c in row.get('detail',{}).get('candidates',[]):
            for key in ['full_forecast_file','early_rejection_witness_file']:
                if c.get(key):witnesses.add(str((g/c[key]).relative_to(R)))
    omit={'full_predictions','nominal_forecasts','rejection_witnesses'};old=plan['groups']['latest_v855'];paths=[p for p in old['files']if(p in witnesses or not any(x in omit for x in Path(p).parts))and Path(p).name!='range_estimate.jsonl']
    selected=dict(files=paths,count=len(paths),bytes=sum((R/p).stat().st_size for p in paths),scope='Complete actual native trajectory, sensors, states, controls, physical model, accepted certificates and audit outcomes; terminal failure573 full saved witnesses retained. Unselected earlier candidate predictions and duplicate range belief cache intentionally omitted.',terminal_failure_step=step,terminal_failure_witnesses=len(witnesses))
    plan['groups']['latest_v855']=selected;dump(OUT/'PLAN.json',plan)
    for p in(OUT/'assets').glob('latest_v855.tar.zst.part*'):p.unlink()
    (OUT/'latest_v855.PACKED.json').unlink()
    old_file=OUT/'DELETE_PLAN.jsonl.gz';temp=OUT/'DELETE_PLAN.latest.jsonl.gz';essential={p for v in plan['groups'].values()for p in v['files']};counts=collections.Counter();sizes=collections.Counter()
    with gzip.open(old_file,'rt')as src,gzip.open(temp,'wt',compresslevel=3)as dst:
        for line in src:
            row=json.loads(line);row['role']='ESSENTIAL_AFTER_VERIFIED_RELEASE'if row['path']in essential else'UNSELECTED_INTERMEDIATE_OR_DUPLICATE';counts[row['role']]+=1;sizes[row['role']]+=row['bytes'];dst.write(json.dumps(row)+'\n')
    temp.replace(old_file)
    summary=dict(core_git_count=plan['core_git_count'],core_git_bytes=plan['core_git_bytes'],groups={k:{a:b for a,b in v.items()if a!='files'}for k,v in plan['groups'].items()},delete_file_counts=dict(counts),delete_logical_bytes=dict(sizes),all_actual_latest_evidence_retained=True,unselected_latest_candidate_pools_intentionally_pruned=True,no_models=True);dump(OUT/'PLAN_SUMMARY.json',summary);print(json.dumps(summary),flush=True)
    for name in ['docs/STORAGE_POLICY.md','records/README.md']:
        p=R/name;text=p.read_text().replace('最新开发完整证据','最新开发完整实际轨迹和末失败见证').replace('最新V855保留完整实际运行及原保存审核所用记录','最新V855保留完整实际运行、已执行控制合同、独立审核结果和末失败见证，早期未选候选池裁剪')
        p.write_text(text)
if __name__=='__main__':main()
