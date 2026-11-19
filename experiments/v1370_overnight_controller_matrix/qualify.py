"""Frozen matrix/dependency, safe-failure, deadline and archive checks; no models."""
import ast
import copy
import gzip
import hashlib
import os
import shutil
import tarfile
from component_context import *
from relay_policy import classify,eligible,FUNCTIONAL
from finalize import Parts,Reader

def main():
    tasks=read(C/'TASKS.json');checks={};assert len(tasks)==271 and len({t['task_id'] for t in tasks})==271
    assert [sum(t['stage']==s for t in tasks) for s in ['component','static','dynamic']]==[7,8,256]
    phases=read(C/'PHASES.json')
    for phase in phases:
        original=read(R/phase['source']);assert all(original[k]==phase[k] for k in ['seed','phase','slot'])
    checks['original_WE8_phases_preserved_no_seed_selection']=True
    assert sha(C/'rpp_default_params.json')==sha(R/'experiments/v1368_rolling_map_entry/rpp_params.json')
    assert sha(C/'coherent_mppi_params.json')==sha(R/'experiments/v1368_rolling_map_entry/mppi_params.json')
    assert read(R/'runs/v1369_guard_audit_runtime/PRODUCER_AUDIT.json')['supplemental_full_audit_passed']
    old_task=read(R/'experiments/v1368_rolling_map_entry/TASKS.json')[0];first=tasks[0]
    for name in ['reference_path','center_reference_path','origin_body','origin_native_tick','seed','phase','causal_ball','component_goal_xy']:assert first[name]==old_task[name]
    checks['qualified_RPP_main_exact_input_parameter_reuse_not_new_sample']=True
    for config in read(C/'CAMPAIGN_CONFIG.json')['configs']:
        p=read(C/(config['branch']+'_params.json'))['controller_server']['ros__parameters']
        assert p['goal_checker']['xy_goal_tolerance']==.08
        if config['kind']=='rpp':assert p['RPP']['lookahead_dist']==config['lookahead_m'] and p['RPP']['desired_linear_vel']==.1
        else:assert p['Deadband']['vx_max']==.1 and p['Deadband']['batch_size']==1000
    checks['fixed_four_configs_with_same_vehicle_speed_and_goal_gates']=True
    prior=R/'runs/v858_nav2_verified/v1368/rpp_recovery_main'
    row=dict(native=read(prior/'RESULT.json'),ros=read(prior/'ROS_RESULT.json'),audit=read(R/'runs/v1369_guard_audit_runtime/PRODUCER_AUDIT.json')['audit'])
    assert classify(row)=='PASSED'
    bad=copy.deepcopy(row);bad['native']['passed']=False;bad['ros']['passed']=False
    for key in FUNCTIONAL:
        if key in bad['audit']['checks']:bad['audit']['checks'][key]=False
    bad['audit']['passed']=False;assert classify(bad)=='FUNCTIONAL_FAILURE_SAFE_COMPLETE'
    for label,alter in [('safety',lambda x:x['audit']['checks'].__setitem__('actual_clearance',False)),('source',lambda x:x['native'].__setitem__('source_unchanged',False)),('ROS_error',lambda x:x['ros'].__setitem__('error','injected')),('unknown',lambda x:x['native'].__setitem__('new_actual_native',None)),('missing_audit',lambda x:x.__setitem__('audit',None))]:
        x=copy.deepcopy(row);alter(x);assert classify(x) not in ['PASSED','FUNCTIONAL_FAILURE_SAFE_COMPLETE'],label
    completed={'REUSED_V1368_RPP_MAIN':'PASSED'}
    assert eligible(first,completed)
    for task in tasks[1:]:
        if task['stage']!='component':assert not eligible(task,completed)
    completed.update({t['task_id']:'PASSED' for t in tasks if t['stage']=='component'})
    assert all(eligible(t,completed) for t in tasks if t['stage']=='static' and t['role']=='main')
    checks['safe_functional_failure_relay_and_safety_evidence_stop_and_dependencies']=True
    tree=ast.parse((C/'campaign.py').read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='monitor']
    assert len(calls)==1 and ast.unparse(calls[0].args[0])=='[peer, native]'
    checks['monitor_peer_order_preserved']=True
    assert not (O/'ROUND_WINDOW.json').exists() and not (O/'APPROVAL.json').exists()
    try:authorize(first,{})
    except (AssertionError,FileNotFoundError):pass
    else:raise AssertionError('UNLAUNCHED_MODEL_AUTHORITY_ACCEPTED')
    checks['models_denied_before_one_real_locked_launch']=True
    reserved=set(read(C/'CAMPAIGN_CONFIG.json')['stage_reserved_cpus_and_siblings'])
    for cpu in [2,3,4,5]:
        siblings=set(map(int,Path('/sys/devices/system/cpu/cpu%d/topology/thread_siblings_list'%cpu).read_text().strip().split(',')))
        assert not siblings & reserved
    checks['phase_cores_not_siblings_of_user_declared_Stage_cores']=True
    # A >32MiB incompressible member tests real streaming chunk boundaries,
    # gzip decode and member SHA without any vehicle or controller.
    fixture=O/'archive_fixture';fixture.mkdir(exist_ok=False);data=os.urandom(33*1024**2+17);expected=hashlib.sha256(data).hexdigest();source=fixture/'payload';source.write_bytes(data);parts=fixture/'parts';parts.mkdir()
    writer=Parts(parts,0,100*1024**2)
    with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3) as compressor, tarfile.open(fileobj=compressor,mode='w|') as archive:
        info=tarfile.TarInfo('payload');info.size=len(data)
        with source.open('rb') as stream:archive.addfile(info,stream)
    writer.finish_part();assert len(writer.parts)==2 and all(p['bytes']<=32*1024**2 for p in writer.parts)
    with tarfile.open(fileobj=Reader([parts/p['name'] for p in writer.parts]),mode='r|gz') as archive:
        member=next(iter(archive));assert hashlib.sha256(archive.extractfile(member).read()).hexdigest()==expected
    limited=Parts(fixture,40*1024**2,100*1024**2)
    try:limited.write(b'limit')
    except AssertionError:pass
    else:raise AssertionError('ARCHIVE_RESERVE_NOT_ENFORCED')
    shutil.rmtree(fixture)
    checks['streaming32MiB_reassembly_memberSHA_and_storage_pressure_rejection']=True
    assert sources()
    proof=dict(passed=all(checks.values()),checks=checks,models=0,physical_native=0,maximum_component_tasks=7,maximum_navigation_tasks=264,planned=271,ordinary_failure_advances=True)
    dump(O/'QUALIFICATION.json',proof);print(json.dumps(proof))

if __name__=='__main__':main()
