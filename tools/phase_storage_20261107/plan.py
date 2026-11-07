"""Select essential Phase evidence and summaries before cloud publication/cleanup."""
import collections,gzip,hashlib,json,os,stat,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
OUT=R/'runs/storage_cleanup_20261107'
EXCLUDE_PARTS={'__pycache__','.git','vendor'}
SUMMARY_NAMES={'result.json','RESULT.json','RESULTS.json','COMPLETION.json','ERROR.json','ROUND_WINDOW.json','LEDGER.json','FINALIZED.json','FINAL_INDEPENDENT_AUDIT.json','AUTHORIZATION.json','PREFLIGHTS.json','SOURCE_FREEZE.json','DOCUMENT_FREEZE.json','TASK_LIST.json','LOCKED_TASK_LIST.json','REGISTERED_TASKS.json','QUALIFICATION.json','OUTPUT_QUALIFICATION.json','PREPARED.json','CLOSED_REVIEW.json','STATIC_PROTOCOL.json','DYNAMIC_PROTOCOL.json','INITIALIZATION_PROVENANCE.json','HORIZON_CONTRACT.json'}
CORE_DIRS={'experiments','runtime','current','docs','manifests','tools','.github'}
ROOT_EXCLUDE={'.git','.git-pre-cleanup','.git-thin-tmp','runs','evidence','work'}

def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def walk(root):
    if not root.exists():return
    for folder,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if d not in EXCLUDE_PARTS)
        for name in sorted(files):
            p=Path(folder)/name
            if p.is_symlink():
                if not p.resolve().is_relative_to(R):continue
            if p.is_file():yield p

def rel(p):return p.relative_to(R).as_posix()

def main():
    OUT.mkdir(exist_ok=True);groups={};core=set();summary=set()
    for p in R.iterdir():
        if p.name in ROOT_EXCLUDE:continue
        if p.is_file()and p.name not in {'.DS_Store'}:core.add(rel(p))
        elif p.is_dir()and p.name in CORE_DIRS:
            core.update(rel(x)for x in walk(p)if x.suffix not in {'.pyc','.pyo','.tmp'}and x.stat().st_size<90*1024**2)
    core.add('runs/v648_static_unknown/execution.lock')
    core.update(x['destination']for x in json.loads((R/'manifests/source_provenance.json').read_text()))
    for name in ['best_verified_rescue','phase22_formal','harm_counterexample','current_v647']:core.update(rel(x)for x in walk(R/'evidence'/name))
    proposer=R/'runs/v690_visible_eight_meter/training_8m'
    core.update(rel(x)for x in walk(proposer))
    # Retain compact actual outcomes/provenance from all closed historical batches.
    for p in walk(R/'runs'):
        if p.is_relative_to(OUT):continue
        if p.stat().st_size<=5*1024**2 and(p.name in SUMMARY_NAMES or p.name.endswith('_AUDIT.json')or(p.suffix=='.md'and len(p.relative_to(R/'runs').parts)<=4)):
            summary.add(rel(p))
    groups['latest_v855']=set(rel(x)for x in walk(R/'runs/v855_renewal_worker'))
    groups['latest_v855'].update(rel(x)for x in walk(R/'runs/v855_renewal_progress')if not any(y in x.relative_to(R/'runs/v855_renewal_progress').parts for y in ['qualification','scheduler_qualification']))
    groups['static_acceptance_v657']=set(rel(x)for x in walk(R/'evidence/static_acceptance_v657_20261101'))
    groups['verified_three_route_v827']=set(rel(x)for x in walk(R/'evidence/rpccr_v827_goal_route_validation_20261105')if 'transport'not in x.relative_to(R/'evidence/rpccr_v827_goal_route_validation_20261105').parts)
    # Full preceding reference run supplies actual original prefix/components and audit fixture.
    groups['reproduction_inputs']=set(rel(x)for x in walk(R/'runs/v851_profile_output_worker'))
    inputs=json.loads((R/'runs/v855_renewal_progress/REVISION_INPUT_SHA.json').read_text());groups['reproduction_inputs'].update(inputs)
    for source in ['runs/v853_maneuver_worker/v853_B64_main_slot01/paired/STATIC_PROTOCOL.json','runs/v853_maneuver_worker/v853_B64_main_slot01/paired/geometry_memory/motion_estimate.jsonl']:
        if(R/source).exists():groups['reproduction_inputs'].add(source)
    # Failed fresh confirmation: keep actual states/sensors/accepted contracts and audits,
    # discard unselected rollout/debug pools. It remains NOT_PASSED.
    omit={'full_predictions','rejection_witnesses','nominal_forecasts','source_snapshot','shadow_handover_certificates'}
    groups['failed_confirmation_v828']=set(rel(x)for x in walk(R/'runs/v828_goal_dynamic_confirmation')if not any(y in omit for y in x.relative_to(R/'runs/v828_goal_dynamic_confirmation').parts)and x.name not in {'control_decisions.jsonl','range_estimate.jsonl'})
    # Keep established pre-migration milestones; these are small curated records.
    groups['milestones']=set()
    for directory in ['evidence/best_verified_rescue','evidence/phase22_formal','evidence/harm_counterexample','evidence/current_v647','evidence/rpccr_no_dynamic_five_v805_20261104_supplement']:
        groups['milestones'].update(rel(x)for x in walk(R/directory))
    # Summaries live in Git; archive groups need not duplicate them.
    core|=summary
    taken=set(core)
    for name,paths in groups.items():groups[name]=sorted(paths-taken);taken.update(paths)
    selected={k:dict(files=v,bytes=sum((R/p).stat().st_size for p in v),count=len(v))for k,v in groups.items()}
    for name in sorted(core):
        assert(R/name).exists()and not any(x in Path(name).parts for x in ['.git','vendor'])
    stats=dict(created_unix=time.time(),repo='frank8763/phase-',root=str(R),core_git_files=sorted(core),core_git_count=len(core),core_git_bytes=sum((R/p).stat().st_size for p in core),groups=selected,keep_local_model_paths=sorted(rel(x)for x in walk(proposer)),no_models_started=True,public_remote_history_preserved=True,unpublished_large_duplicate_history_not_uploaded=True)
    dump(OUT/'PLAN.json',stats)
    with gzip.open(OUT/'DELETE_PLAN.jsonl.gz','wt')as stream:
        counts=collections.Counter();sizes=collections.Counter()
        for base in [R/'runs',R/'evidence']:
            for p in walk(base):
                if p.is_relative_to(OUT)or rel(p)in core:continue
                s=p.lstat();needed=rel(p)in taken;kind='ESSENTIAL_AFTER_VERIFIED_RELEASE'if needed else'UNSELECTED_INTERMEDIATE_OR_DUPLICATE';stream.write(json.dumps(dict(path=rel(p),bytes=s.st_size,inode=s.st_ino,device=s.st_dev,mtime_ns=s.st_mtime_ns,role=kind))+'\n');counts[kind]+=1;sizes[kind]+=s.st_size
    dump(OUT/'PLAN_SUMMARY.json',dict(core_git_count=len(core),core_git_bytes=stats['core_git_bytes'],groups={k:{x:y for x,y in v.items()if x!='files'}for k,v in selected.items()},delete_file_counts=dict(counts),delete_logical_bytes=dict(sizes),delete_rule='Needed records only after complete remote digest and streamed-download verification; user authorized deleting unselected intermediates.',note='Logical bytes include hardlinks; actual freed space measured from filesystem afterwards.'))
    print(json.dumps(json.loads((OUT/'PLAN_SUMMARY.json').read_text())),flush=True)
if __name__=='__main__':main()
