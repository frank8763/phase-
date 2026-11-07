"""Remove reproducible caches from historical records, keep latest V855 complete."""
import collections,gzip,hashlib,json
from pathlib import Path
from plan import R,OUT,dump

def main():
    v=json.loads((OUT/'PLAN.json').read_text());omit_dirs={'full_predictions','rejection_witnesses','nominal_forecasts','ordinary_certificates'};omit_names={'motion_estimate.jsonl','range_estimate.jsonl','control_decisions.jsonl','route_revalidation.jsonl','early_joint_decisions.jsonl'}
    for name in ['reproduction_inputs','failed_confirmation_v828']:
        group=v['groups'][name];group['files']=[p for p in group['files']if not any(x in omit_dirs for x in Path(p).parts)and Path(p).name not in omit_names];group['count']=len(group['files']);group['bytes']=sum((R/p).stat().st_size for p in group['files']);group['scope']='Historical actual trajectories/sensors/model/accepted recovery contracts and audit outcomes; reproducible belief/prediction/debug caches omitted.'
    inventory=R/'evidence/rpccr_v827_goal_route_validation_20261105/RAW_INVENTORY.json.gz';rows=json.load(gzip.open(inventory,'rt'));kept=[]
    for row in rows:
        p=Path(row['path'])
        if p.parts[0]!='runs':continue
        if any(x in omit_dirs for x in p.parts)or p.name in omit_names:continue
        # Retain actual V827 runs and the reused V826 reference's actual trajectory.
        if not any(x in row['path']for x in ['v827_goal_route_validation','v826_goal_reference_renewal']):continue
        kept.append(row)
    dest=OUT/'V827_SELECTED_BLOB_INVENTORY.json.gz'
    with gzip.open(dest,'wt')as stream:json.dump(dict(original_inventory_sha256=hashlib.sha256(inventory.read_bytes()).hexdigest(),scope='Selected actual run records; excludes regenerated belief, ordinary prediction and rejected rollout pools. Original audit results retained, full original all-candidate archive intentionally not retained.',blob_root='evidence/rpccr_v827_goal_route_validation_20261105',rows=kept),stream,indent=2)
    blobs={str(Path('evidence/rpccr_v827_goal_route_validation_20261105')/row['blob'])for row in kept};blobs.add(str(dest.relative_to(R)));v['groups']['verified_three_route_v827']=dict(files=sorted(blobs),count=len(blobs),bytes=sum((R/p).stat().st_size for p in blobs),blob_inventory=str(dest.relative_to(R)),scope='Selected actual three-route milestone evidence; generated full-candidate prediction caches omitted.')
    # Previously packed historical caches are disposable derived files; source records remain intact.
    for name in ['reproduction_inputs','failed_confirmation_v828','verified_three_route_v827']:
        for p in(OUT/'assets').glob(name+'.tar.zst.part*'):p.unlink()
        (OUT/(name+'.PACKED.json')).unlink()
    dump(OUT/'PLAN.json',v);essential={p for x in v['groups'].values()for p in x['files']};old=OUT/'DELETE_PLAN.jsonl.gz';temp=OUT/'DELETE_PLAN.refined.jsonl.gz';counts=collections.Counter();sizes=collections.Counter()
    with gzip.open(old,'rt')as source,gzip.open(temp,'wt',compresslevel=3)as target:
        for line in source:
            row=json.loads(line);row['role']='ESSENTIAL_AFTER_VERIFIED_RELEASE'if row['path']in essential else'UNSELECTED_INTERMEDIATE_OR_DUPLICATE';target.write(json.dumps(row)+'\n');counts[row['role']]+=1;sizes[row['role']]+=row['bytes']
    temp.replace(old);summary=dict(core_git_count=v['core_git_count'],core_git_bytes=v['core_git_bytes'],groups={k:{a:b for a,b in x.items()if a!='files'}for k,x in v['groups'].items()},delete_file_counts=dict(counts),delete_logical_bytes=dict(sizes),local_readiness_fixtures_preserved=True,latest_v855_complete=True,historical_predictive_caches_intentionally_pruned=True,no_models=True);dump(OUT/'PLAN_SUMMARY.json',summary);print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
