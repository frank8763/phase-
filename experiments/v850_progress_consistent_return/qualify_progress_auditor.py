"""Actual new audit entry on an explicitly derived predetection fixture, no models."""
import copy,gzip,json,os,signal,subprocess,sys
from pathlib import Path
from common import R,W,C,ROOT,dump,read
sys.path.insert(0,str(W))
from progress_contract import context,assess,summarize
from types import SimpleNamespace
import numpy as np


def main():
    root=ROOT/'progress_auditor_qualification';root.mkdir(exist_ok=False)
    base=R/'runs/v848_goal_first_worker/v848_main_slot02/paired';source=base/'geometry_memory'
    pair=root/'saved_predetection_fixture';cell=pair/'geometry_memory';cell.mkdir(parents=True)
    for name in ['STATIC_PROTOCOL.json']:(pair/name).symlink_to(base/name)
    (cell/'ACTUATOR_COMMAND_CONTRACT.json').symlink_to(source/'ACTUATOR_COMMAND_CONTRACT.json')
    result=read(source/'result.json');result.update(source_revision='V850_DERIVED_AUDIT_FIXTURE_NOT_NEW_NAVIGATION',public_steps=32,physics_steps=256);dump(cell/'result.json',result)
    records=[json.loads(s)for s in(source/'v648_execution.jsonl').open()][:32]
    admissions=[json.loads(s)for s in(source/'model_admission.jsonl').open()][:32]
    assert all(x['status']=='MODEL_SAFE_COMMAND'and not x.get('certified_backup_handover')for x in admissions)
    (cell/'v648_execution.jsonl').write_text(''.join(json.dumps(r)+'\n'for r in records));(cell/'model_admission.jsonl').write_text(''.join(json.dumps(r)+'\n'for r in admissions))
    states=[json.loads(s)for s in(source/'motion_estimate.jsonl').open()][:32];assert all(x['center']is None for x in states)
    (cell/'motion_estimate.jsonl').write_text(''.join(json.dumps(r)+'\n'for r in states))
    folder=cell/'progress_certificates';folder.mkdir()
    protocol=read(pair/'STATIC_PROTOCOL.json')
    for step in range(32):
        z=np.load(source/'ordinary_certificates'/f'certificate_{step:04d}.npz')
        initial=np.asarray(records[step-1]['qpos_full'])if step else np.asarray(protocol['start_qpos'])
        c={k:z[k]for k in ['qpos','qvel','controls','initial_qpos','initial_qvel','prefix_command']}
        c.update(created_step=step,created_time=float(z['created_time']),prefix_initial_qpos=initial)
        real=SimpleNamespace(qpos=initial);ctx=context(real,{'center':None},None,None,0,step);summarize(c,ctx,assess(ctx,c['qpos'][-1,:2]),'LEGACY_PHASE')
        with gzip.open(folder/f'certificate_{step:04d}.json.gz','xt')as stream:json.dump(c,stream,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item())
    dump(cell/'CONTROL_LATENCY.json',dict(records=[dict(step=i,decision_wall_s=.1)for i in range(32)],period_s=.08,over_period_count=32,synthetic_fixture_not_performance=True))
    guard=(R/'REVIEW_PENDING').read_bytes();cases=[]
    def run(label,expected):
        with(root/(label+'.console')).open('x')as stream:
            process=subprocess.Popen([str(R/'run_phase.sh'),str(C.relative_to(R)/'audit_entry.py'),'--write-root',str(pair),'audit_progress.py',str(pair)],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=process.wait(timeout=60)
            finally:
                if process.poll()is None:os.killpg(process.pid,signal.SIGKILL);process.wait()
        assert(code==0)==expected,(label,code);cases.append(dict(case=label,expected_pass=expected,exit=code))
    try:
        (R/'REVIEW_PENDING').unlink();run('actual_entry_positive',True)
        path=folder/'certificate_0020.json.gz';raw=path.read_bytes()
        with gzip.open(path,'rt')as stream:c=json.load(stream)
        c['progress_contract']['mode']='PROGRESS'
        with gzip.open(path,'wt')as stream:json.dump(c,stream)
        run('forged_active_progress',False);path.write_bytes(raw)
        wrong=copy.deepcopy(records);wrong[20]['ctrl'][0]+=.01;(cell/'v648_execution.jsonl').write_text(''.join(json.dumps(r)+'\n'for r in wrong));run('actual_control_tamper',False)
        (cell/'v648_execution.jsonl').write_text(''.join(json.dumps(r)+'\n'for r in records));run('restored_fixture',True)
        dump(root/'RESULT.json',dict(passed=True,cases=cases,fixture_source=str(base.relative_to(R)),fixture_scope='32 saved predetection records with derived metadata and synthetic timing, not new navigation or performance',model_constructions=0,integrations=0))
    finally:(R/'REVIEW_PENDING').write_bytes(guard)


if __name__=='__main__':main()
