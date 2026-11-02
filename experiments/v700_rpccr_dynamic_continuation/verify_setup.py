"""Read-only preparation: fixed provenance, legal schedule and closed prerequisites."""
import fcntl
import gzip
import hashlib
import json
from pathlib import Path

repo=Path(__file__).resolve().parents[2]
own=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=read(repo/'experiments/v699_dynamic_packet_audit/SOURCE_FREEZE.json')['files']
assert all(sha(repo/n)==h for n,h in prior.items()),'OLD_SCIENCE_OR_GUARD_CHANGED_BEFORE_AUTHORIZED_REMOVAL'
assert read(repo/'RPCCR_DYNAMIC_AUDIT_REPAIR_CLOSED_20261102.json')['status']=='V699_ZERO_AUDIT_REPAIR_VALIDATED_CLOSED'
assert read(repo/'runs/v699_dynamic_packet_audit/MISSING_KEY_NEGATIVE_TEST.json')['status']=='MISSING_KEY_REJECTION_VERIFIED'
assert read(repo/'runs/v698_rpccr_dynamic_confirmation/FINAL_INDEPENDENT_AUDIT.json')['status']=='NOT_PASSED'
tasks=read(own/'TASK_LIST.json');plan=read(own/'EXECUTION_PLAN.json')
assert sha(own/'TASK_LIST.json')==sha(repo/'experiments/v698_rpccr_dynamic_confirmation/TASK_LIST.json')
assert [t['slot'] for t in tasks]==list(range(1,25))
assert plan['imported_main_slots']+plan['new_main_slots']==list(range(1,25))
assert plan['conditional_repeat_slots']==[1,8,20] and len(plan['new_main_slots'])+3==14
original=read(repo/'runs/v698_rpccr_dynamic_confirmation/confirmation01/RESULTS.json')
physical=read(repo/'runs/v698_rpccr_dynamic_confirmation/FINAL_INDEPENDENT_AUDIT.json')['records']
assert len(original)==13 and [x['task'] for x in original]==tasks[:13]
assert all(x['physical_evidence_passed'] for x in physical)
assert all(read(repo/('runs/v699_dynamic_packet_audit/slot%02d/DISCOVERY_CHAIN_AUDIT_V699.json'%x['task']['slot']))['status']=='PASS' for x in original)
assert original[-1]['functional_passed'] is False and physical[-1]['physical_evidence_passed'], 'SLOT13_ORIGINAL_STOP_MUST_BE_PRESERVED'
assert not (repo/'runs/v700_rpccr_dynamic_continuation/ROUND_WINDOW.json').exists()
for task in tasks:
    for prefix in ['v700_slot','v700_repeat_slot']:
        assert not (repo/'runs/v697_rpccr_dynamic_initialization'/('%s%02d'%(prefix,task['slot']))).exists()
for directory in ['rpccr_dynamic_confirmation_v698_20261102','rpccr_dynamic_audit_v699_20261102']:
    archive=repo/'evidence'/directory
    for row in read(archive/'MANIFEST.json'):
        assert sha(archive/row['path'])==row['sha256']
    with gzip.open(archive/'RAW_INVENTORY.json.gz','rt') as stream:inventory=json.load(stream)
    for row in inventory:
        data=(archive/row['blob']).read_bytes()
        raw=gzip.decompress(data) if row['stored_encoding']=='gzip' else data
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for path in own.glob('*.py'):compile(path.read_text(),str(path),'exec')
with (repo/'runs/v648_static_unknown/execution.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
print(json.dumps({'status':'V700_PREPARATION_VALIDATED_ZERO_INTEGRATION',
                  'original_frozen_inputs_unchanged':len(prior),'same_fixed_tasks':24,
                  'imported_old_trajectories':13,'maximum_new_main':11,'fixed_repeats':[1,8,20],
                  'old_slot13_failure_preserved':True,'old_complete_archives_verified':2,
                  'simulation_steps':0,'training_updates':0,'review_guard_present':(repo/'REVIEW_PENDING').exists()}))
