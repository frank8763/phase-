"""Reconstruct every actually selected new progress mode and retained commitment."""
import argparse,gzip,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from progress_record_independent import check


def audit(pair):
    cell=pair/'geometry_memory';read=lambda p:json.loads(p.read_text())
    lines=lambda p:[json.loads(s)for s in p.open()]if p.exists()else[]
    result=read(cell/'result.json');assert result['source_revision'].startswith('V850')
    execution=lines(cell/'v648_execution.jsonl');ad=lines(cell/'model_admission.jsonl')
    protocol=read(pair/'STATIC_PROTOCOL.json');goal=np.asarray(protocol['goal_xy']);ids=read(cell/'ACTUATOR_COMMAND_CONTRACT.json')['ids']
    states={r['step']:r for r in lines(cell/'motion_estimate.jsonl')}
    snapshots={};records=[]
    def load(p):
        with gzip.open(p,'rt')as stream:return json.load(stream)
    for directory in ['progress_certificates','handover_certificates','recovery_contracts']:
        for p in (cell/directory).glob('*.gz'):
            c=load(p);snapshots[c['created_step']]=c
    selected=[r for r in ad if r['status']=='MODEL_SAFE_COMMAND'or r.get('certified_backup_handover')]
    for row in selected:
        step=row['step'];c=snapshots[step];proof=c['progress_contract'];ctx=proof['context']
        assert step in states
        active=states[step]['center']is not None and (bool(row.get('certified_backup_handover'))or row.get('active_gear')==1)
        assert ctx['active']==active,'PROGRESS_APPLICABILITY_DISGUISED_AS_LEGACY'
        assert ctx['role']==('BACKUP_RETURN'if row.get('certified_backup_handover')else'ORDINARY')
        assert np.array_equal(ctx.get('goal_xy',goal),goal)
        old=None if ctx['old_created_step']is None else snapshots[ctx['old_created_step']]
        previous=execution[step-1]if step else None
        real=SimpleNamespace(qpos=np.asarray(previous['qpos_full']if previous else protocol['start_qpos']),qvel=np.asarray(previous['qvel_full']if previous else np.zeros(len(c['initial_qvel']))),time=c['created_time'])
        verified=check(c,real,old,ctx['old_cursor'])
        assert np.array_equal(c['prefix_command'],np.asarray(execution[step]['ctrl'])[ids])
        assert np.max(abs(np.asarray(c['initial_qpos'])-execution[step]['qpos_full']))<=1e-8
        assert np.max(abs(np.asarray(c['initial_qvel'])-execution[step]['qvel_full']))<=1e-8
        if row.get('certified_backup_handover'):assert verified['mode']!='RECOVERY_ENTRY'and ctx['role']=='BACKUP_RETURN'
        if verified['mode']=='RECOVERY_ENTRY':
            activation=load(cell/'recovery_contracts'/f'contract_{step+1:04d}.json.gz')
            assert activation['activation_step']==step+1 and activation['created_step']==step
            assert np.array_equal(activation['qpos'],c['qpos'])and np.array_equal(activation['controls'],c['controls'])
        records.append(dict(step=step,**verified))
    retained=lines(cell/'progress_retained.jsonl');events={r['step']:r for r in lines(cell/'early_joint_decisions.jsonl')}
    for row in retained:
        step=row['step'];old=snapshots[row['old_created_step']];cursor=row['old_cursor'];q=np.asarray(old['initial_qpos']if cursor==0 else old['qpos'][cursor-1]);v=np.asarray(old['initial_qvel']if cursor==0 else old['qvel'][cursor-1])
        assert row['hidden_world_geometry_used']is False and 0<=cursor<320
        assert np.max(abs(q-row['real_qpos']))<=1e-8 and np.max(abs(v-row['real_qvel']))<=1e-8
        assert abs(row['real_time']-old['start_time']-.01*cursor)<=1e-8
        assert np.array_equal(row['old_terminal_qpos'],old['qpos'][-1])
        gate=ad[step];assert gate['status']=='RETAINED_REVERSE_BRAKE_CONTRACT'and gate['retained_from_step']==old['created_step']and gate['contract_native_cursor']==cursor
        assert np.array_equal(np.asarray(execution[step]['ctrl'])[ids],old['controls'][cursor])
        event=events.get(step)
        if event is not None:assert event['selected_rank']is None and all(p['summary']is None for p in event['probes'])
        else:
            nom=next(r for r in lines(cell/'control_decisions.jsonl')if r['step']==step and r['stage']=='NOMINAL'and r['candidate_role']=='ORDINARY')
            count=0
            for c in nom['candidates']:
                if c['reason']is not None:continue
                z=np.load(cell/'nominal_forecasts'/c['nominal_saved_forecast'])
                gain=np.linalg.norm(np.asarray(row['real_qpos'])[:2]-goal)-np.linalg.norm(z['poses'][-1,:2]-goal)
                count+=np.mean(c['first_command'][2:])>=0 and gain>=.02
            assert count==0
    assert records and len(selected)==len(records)
    latency=read(cell/'CONTROL_LATENCY.json');samples=[r['decision_wall_s']for r in latency['records']]
    assert len(samples)==len(execution)and all(np.isfinite(samples))and min(samples)>=0
    assert latency['period_s']==.08 and latency['over_period_count']==sum(v>.08 for v in samples)
    return dict(status='PROGRESS_CONTRACT_SELECTION_PASS',records=records,retained_commits=len(retained),checks=dict(selected_full_progress=True,old_certificate_join=True,negative_progress_only_explicit_recovery=True,retained_actual_command=True,latency_records_complete=True),latency={k:v for k,v in latency.items()if k!='records'},new_models=0,new_integrations=0,global_arrival_or_realtime_theorem=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('pair',type=Path);args=parser.parse_args()
    value=audit(args.pair);(args.pair/'PROGRESS_CONTRACT_AUDIT.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({k:v for k,v in value.items()if k!='records'}))
