"""Independent persisted gates/counts/report and lossless archive; zero models."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('ZERO_MODEL_FINALIZER')
sys.meta_path.insert(0,NoModels())
import fcntl,gzip,json,os,shutil,time
from common import *
from repeat import compare


def archive(report):
    target=R/'evidence/rpccr_v854_daytime_input_continuation_20261107';assert not target.exists();target.mkdir();(target/'blobs').mkdir();files={R/p for p in read(C/'CANDIDATE_FREEZE.json')['files']}
    for directory in [C,W,ROOT,RAW]:
        if directory.exists():files.update(p for p in directory.rglob('*')if p.is_file()and p.suffix not in['.lock','.pyc']and '__pycache__'not in p.parts and p.name not in['finalize.console','campaign.console','transport.console'])
    files.update([report,R/'CURRENT_EXPERIMENT.json',R/'REVIEW_PENDING']);inventory=[]
    previous=R/'evidence/rpccr_v851_profile_output_20261107/blobs'
    for p in sorted(files):
        h=sha(p);encoding='identity'if p.suffix=='.gz'else'gzip';name=h+('.raw'if encoding=='identity'else'.gz');blob=target/'blobs'/name
        if not blob.exists():
            prior=previous/name
            if prior.exists():os.link(prior,blob)
            elif encoding=='identity':os.link(p,blob)
            else:
                with p.open('rb')as source,gzip.GzipFile(filename=str(blob),mode='xb',mtime=0)as destination:shutil.copyfileobj(source,destination,1048576)
        inventory.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=h,encoding=encoding,blob='blobs/'+name))
    with gzip.open(target/'RAW_INVENTORY.json.gz','xt')as f:json.dump(inventory,f,indent=2)
    verified=set();transport=[]
    import hashlib
    for row in inventory:
        blob=target/row['blob']
        if row['blob']not in verified:
            h=hashlib.sha256();size=0
            with(blob.open('rb')if row['encoding']=='identity'else gzip.open(blob,'rb'))as f:
                for b in iter(lambda:f.read(1048576),b''):size+=len(b);h.update(b)
            assert h.hexdigest()==row['sha256']and size==row['bytes'];verified.add(row['blob'])
            if blob.stat().st_size>90*1024**2:
                dest=target/'transport';dest.mkdir(exist_ok=True);parts=[];combined=hashlib.sha256()
                with blob.open('rb')as f:
                    for i in range((blob.stat().st_size+32*1024**2-1)//(32*1024**2)):
                        p=dest/(blob.name+f'.part{i:03d}');p.write_bytes(f.read(32*1024**2));parts.append(dict(path=str(p.relative_to(target)),bytes=p.stat().st_size,sha256=sha(p)))
                        with p.open('rb')as part:
                            for b in iter(lambda:part.read(1048576),b''):combined.update(b)
                assert combined.hexdigest()==sha(blob);transport.append(dict(original=row['blob'],bytes=blob.stat().st_size,sha256=sha(blob),parts=parts))
        assert sha(R/row['path'])==row['sha256']
    dump(target/'TRANSPORT.json',transport);dump(target/'VERIFIED.json',dict(source_and_decompressed_sha_verified=True,raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),originals_retained=True,transport_reassembly_verified=True))
    (target/'.gitignore').write_text(''.join('/'+x['original']+'\n'for x in transport))
    return dict(archive=str(target.relative_to(R)),source_and_decompressed_sha_verified=True,raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),large_blobs=len(transport),originals_retained=True)


def main():
    lock=(ROOT/'finalizer.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if(ROOT/'FINALIZED.json').exists():print('ALREADY_FINALIZED_NO_OVERWRITE');return
    assert read(ROOT/'ROUND_WINDOW.json')['round_closed']and(R/'REVIEW_PENDING').read_bytes()==(ROOT/'REVIEW_PENDING.before').read_bytes()
    with(R/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
    source_ok=True
    try:unchanged()
    except AssertionError:source_ok=False
    expected=read(ROOT/'QUALIFICATION.json')['expected_audit_statuses'];variants=[];counts=dict(navigation_native=0,navigation_private_native=0,navigation_replay_native=0,component_old_replay_native=0,component_private_native=0,component_actual_native=0,component_repeat_native=0,backend_old_replay_native=0,backend_private_native=0);exact={k:True for k in counts}
    for variant,commit in VARIANTS:
        phase=ROOT/variant;rows=read(phase/'RESULTS.json')if(phase/'RESULTS.json').exists()else[];records=[]
        for row in rows:
            pair=R/row['run'];result=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None;partial=read(pair/'geometry_memory/interrupted.json')if(pair/'geometry_memory/interrupted.json').exists()else None;actual=result or partial or{};replay=read(pair/'NATIVE_REPLAY_AUDIT.json')if(pair/'NATIVE_REPLAY_AUDIT.json').exists()else{}
            for label,key in [('navigation_native','physics_steps'),('navigation_private_native','prediction_steps')]:
                value=actual.get(key);counts[label]+=value if isinstance(value,int)else 0;exact[label]&=result is not None and isinstance(value,int)
            value=replay.get('replay_integration_steps');counts['navigation_replay_native']+=value if isinstance(value,int)else 0;exact['navigation_replay_native']&=isinstance(value,int)
            gates={}
            for script,filename,_ in AUDITS:
                data=read(pair/filename)if(pair/filename).exists()else{};execution=read(pair/(script+'.execution.json'))if(pair/(script+'.execution.json')).exists()else{}
                gates[script]=row.get('audits',{}).get(script)==0 and data.get('status')==expected[script]and all(data.get('checks',{}).values())and execution.get('passed')and execution.get('original_auditor_sha256')==sha(W/script)
                if script=='audit_run.py':gates[script]&=len(execution.get('actual_model_metadata_reads',[]))==1 and execution['actual_model_metadata_reads'][0]['completed_unix']<DEADLINE and not execution.get('metadata_proxy_import_only',True)
            chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')if(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json').exists()else{};failed=[k for k,v in chain.get('checks',{}).items()if not v];physical=bool(source_ok and result and all(gates.values())and replay.get('maximum_full_native_state_ctrl_error',1e30)<=1e-8 and replay.get('replay_integration_steps')==result['physics_steps']and chain and not(set(failed)-FUNCTIONAL_CHECKS));functional=bool(physical and chain['status']=='PASS'and result['strict_safe_arrival']and result['goal_distance_m']<=.45);repeated=None
            if row.get('base')and result is not None:repeated=compare(R/row['base'],pair)
            records.append(dict(name=row['name'],task=row['task'],role=row['role'],run=row['run'],physical_passed=physical,functional_passed=functional,repeat_passed=None if repeated is None else repeated['passed'],repeat=repeated,result=result,audits=gates,functional_failed_checks=failed))
        component=ROOT/('component_'+variant);component_result=read(component/'RESULT.json')if(component/'RESULT.json').exists()else None;component_completion=read(component/'COMPLETION.json')if(component/'COMPLETION.json').exists()else None
        if component_completion:
            for label,key in [('component_old_replay_native','old_replay_native'),('component_private_native','private_native'),('component_actual_native','actual_branch_native'),('component_repeat_native','repeat_branch_native')]:
                value=component_completion['counts'].get(key);counts[label]+=value if isinstance(value,int)else 0;exact[label]&=isinstance(value,int)and(key!='private_native'or component_completion.get('private_count_exact',False))
        passed=bool(component_result and component_result['passed']and complete_gate(records));variants.append(dict(variant=variant,commit_native=commit,component=component_result,development_passed=passed,records=records,main_attempts=sum(x['role']=='MAIN'for x in rows),main_successes=sum(x['role']=='MAIN'and x['functional_passed']for x in records),unexecuted_navigation=6-len(rows)))
    backend=read(ROOT/'cpu_batch_qualification/RESULT.json')if(ROOT/'cpu_batch_qualification/RESULT.json').exists()else None
    if backend:
        counts['backend_old_replay_native']=backend['old_replay_native'];counts['backend_private_native']=backend['private_native']
    elif(ROOT/'cpu_batch_qualification/COMPLETION.json').exists():
        b=read(ROOT/'cpu_batch_qualification/COMPLETION.json');counts['backend_old_replay_native']=b['old_replay_native'];counts['backend_private_native']=b.get('private_native')or 0;exact['backend_private_native']=False
    prior=read(R/'runs/v853_daytime_20261107/FINALIZED.json')
    final=dict(previous_closed_run=dict(path='runs/v853_daytime_20261107',status=prior['status'],counts=prior['counts'],source_and_decompressed_sha_verified=prior['source_and_decompressed_sha_verified']),status='FINITE_THREE_ROUTE_DEVELOPMENT_PASS'if any(x['development_passed']for x in variants)else'NOT_PASSED_OR_INCOMPLETE',root_stop=read(ROOT/'COMPLETION.json')['status'],source_unchanged=source_ok,variants=variants,backend=backend,known_counts=counts,accounts_exact=exact,counts={k:v if exact[k]else None for k,v in counts.items()},new24=0,training_updates=0,real_robot=0,no_statistical_confirmation=True,no_realtime_claim=True,model_initializations=None,review_pending_restored=True,execution_lock_idle=True,models_finalizer=0,integrations_finalizer=0)
    dump(ROOT/'FINAL_INDEPENDENT_AUDIT.json',final);report=R/'docs/RPCCR_DAYTIME_V854_INPUT_CONTINUATION_20261107_REPORT.md';report.write_text('# 2026-11-07截至20:00日间无人值守实验实际报告\n\n'+json.dumps(final,ensure_ascii=False,indent=2)+'\n\n完整主/重复/失败/未执行均分版保留；原1200步失败不重开，新2400步为新开发预算。没有新24、训练、实体机或实时资格声明。20:00后只零模型收尾。\n')
    saved=archive(report);dump(ROOT/'FINALIZED.json',{k:v for k,v in final.items()if k!='variants'}|saved|dict(report=str(report.relative_to(R))));print(json.dumps(read(ROOT/'FINALIZED.json')),flush=True)


if __name__=='__main__':main()
