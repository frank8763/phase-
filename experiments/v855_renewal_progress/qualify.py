"""Actual saved auditors, public write guard and fixed maneuver bridge; no models."""
import ast,copy,gzip,importlib.abc,json,os,shutil,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('PREPARATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
from common import *
import numpy as np


def main():
    out=ROOT/'qualification';resuming=out.exists();out.mkdir(exist_ok=True)
    for folder in [C,W]:
        for p in folder.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    before=(R/'REVIEW_PENDING').read_bytes();guard_hash=sha(R/'REVIEW_PENDING');expected={};saved=R/'runs/v851_profile_output_worker/v851_main_slot01/paired';view=out/'saved_view/paired';view.mkdir(parents=True,exist_ok=True)
    outputs={f for _,f,_ in AUDITS}|{'MANEUVER_AUDIT.json'}
    def ignore(folder,names):return[n for n in names if n in outputs or n.endswith('.execution.json')or n.endswith('.console')]
    if not resuming:
        shutil.copytree(saved,view,dirs_exist_ok=True,copy_function=os.link,ignore=ignore)
        shutil.copytree(saved.parent/'source_snapshot',view.parent/'source_snapshot',copy_function=os.link)
    window=out/'old_window';window.mkdir(exist_ok=True);oldphase=R/'runs/v851_profile_output_continuation/development01'
    for name in ['SOURCE_FREEZE.json','DOCUMENT_FREEZE.json']:shutil.copy2(oldphase/name,window/name)
    records=[]
    for script,filename,_ in AUDITS:
        if script=='audit_maneuver.py':continue
        prior=view/(script+'.execution.json')
        if prior.exists()and(view/filename).exists():
            old=read(prior)
            if old.get('passed')and old['original_auditor_sha256']==sha(W/script):
                v=read(view/filename);assert all(v.get('checks',{}).values());expected[script]=v['status'];records.append(dict(script=script,passed=True,status=v['status'],reused_completed_preparation=True));continue
        args=[sys.executable,'-B',str(C/'audit_entry.py'),'--write-root',str(view)]
        if script=='audit_run.py':args+=['--metadata-proxy']
        args+=[script,str(view)]
        if script=='audit_run.py':args+=['--window',str(window)]
        if script=='audit_projection_learning.py':args+=['--model',str(R/'runs/v690_visible_eight_meter/training_8m/proposer.json')]
        console=out/(script+'.console')
        if console.exists():console.rename(out/(script+f'.interrupted_{int(time.time())}.console'))
        with console.open('x')as stream:p=subprocess.run(args,cwd=R,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
        assert p.returncode==0,(script,'SAVED_INTERFACE_FAILED');v=read(view/filename);assert all(v.get('checks',{}).values());expected[script]=v['status'];records.append(dict(script=script,passed=True,status=v['status']))
    expected['audit_maneuver.py']='COMMON_MANEUVER_AND_ACTUAL_COMMITMENT_PASS'
    assert subprocess.run([sys.executable,'-B',str(C/'qualify_output.py')],cwd=R,timeout=90).returncode==0
    # The actual native bridge is fed old full certificates, not a substitute
    # predictor. Every decision is checked by a separately written loop formula.
    sys.path.insert(0,str(W));from maneuver_policy import assess_offer,decorate
    from audit_maneuver import check_certificate
    pair=saved;cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');trace=read(cell/'trace.json');execution=[json.loads(x)for x in(cell/'v648_execution.jsonl').read_text().splitlines()];plans=[read(p)for p in cell.glob('planning_*.json')];classifications=[]
    for step in [374,399,619,734,865,932,982,1073,1120,1148]:
        c=json.load(gzip.open(cell/'progress_certificates'/f'certificate_{step:04d}.json.gz','rt'));old=execution[step-1];real=SimpleNamespace(qpos=np.asarray(old['qpos_full']),qvel=np.asarray(old['qvel_full']),time=c['created_time']);route=max((p for p in plans if p['step']<=step),key=lambda x:x['step']);reference=dict(path=route['path'],index=trace[step]['path_index'],goal_xy=protocol['goal_xy']);reserved=SimpleNamespace(cache=None,cursor=0);decision=assess_offer(reserved,reference,real,c,c['forecast_state'],step);c['maneuver_contract']=decision;decorate(c,reference,c['forecast_state'],step);independent=check_certificate(c);assert independent['normal_allowed']==decision['normal_allowed'];classifications.append(dict(step=step,**independent))
        forged=copy.deepcopy(c);forged['maneuver_contract']['route_merit_gain_commit_m']+=.1
        try:check_certificate(forged)
        except AssertionError:pass
        else:raise AssertionError('FORGED_MERIT_NOT_REJECTED')
    # Correct and wrong identity paths of the real OS watcher.
    os_cases=[]
    for label,entry,expected_code in [('correct',str(Path(__file__).resolve()),0),('wrong',str(C/'start.py'),1)]:
        p=subprocess.run([sys.executable,'-B',str(C/'os_watch.py'),'--probe-only','--pid',str(os.getpid()),'--entrypoint',entry,'--deadline',str(DEADLINE)],capture_output=True,text=True,timeout=5);assert(p.returncode==0)==(expected_code==0);(out/('os_'+label+'.console')).write_text(p.stdout+p.stderr);os_cases.append(label)
    assert(R/'REVIEW_PENDING').read_bytes()==before
    result=dict(passed=True,status='SAVED_AUDITORS_REAL_OUTPUT_GUARD_AND_MANEUVERS_QUALIFIED',expected_audit_statuses=expected,records=records,fixed_classifications=classifications,negative_forged_merits=10,os_identity_cases=os_cases,review_pending_sha256=guard_hash,models=0,integrations=0,canonical_metadata_proxy_import_only=True,new_native_dynamics_qualified=False)
    dump(ROOT/'QUALIFICATION.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['records','fixed_classifications','expected_audit_statuses']}),flush=True)


if __name__=='__main__':main()
