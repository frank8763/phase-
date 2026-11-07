"""Saved V848/V851 wall-time and actual motion decomposition; no models."""
import gzip,hashlib,importlib.abc,json,signal,sys
from pathlib import Path
import numpy as np
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('OUTCOME_ANALYSIS_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
R=Path(__file__).resolve().parents[2]


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_ANALYSIS_180S')));signal.alarm(180)
    out=R/'runs/v851_outcome_analysis';out.mkdir(exist_ok=False);sources={}
    def read(path):
        raw=path.read_bytes();sources[str(path.relative_to(R))]=hashlib.sha256(raw).hexdigest()
        return json.loads(gzip.decompress(raw)if path.suffix=='.gz'else raw)
    def lines(path):
        raw=path.read_bytes();sources[str(path.relative_to(R))]=hashlib.sha256(raw).hexdigest();return[json.loads(s)for s in raw.splitlines()]
    comparison={}
    for label,relative in [('V848','runs/v848_goal_first_worker/v848_main_slot01/paired'),('V851','runs/v851_profile_output_worker/v851_main_slot01/paired')]:
        pair=R/relative;cell=pair/'geometry_memory';result=read(cell/'result.json');protocol=read(pair/'STATIC_PROTOCOL.json');execution=lines(cell/'v648_execution.jsonl');goal=np.asarray(protocol['goal_xy']);xy=np.asarray([x['qpos_full'][:2]for x in execution]);dist=np.linalg.norm(xy-goal,axis=1)
        assert len(execution)==result['public_steps']==1200 and result['outcome']=='HORIZON'
        comparison[label]={k:result[k]for k in ['elapsed_s','public_steps','physics_steps','prediction_steps','backup_attempts','backup_steps','planning_attempts','planning_wall_s','goal_distance_m']}
        comparison[label].update(closest_goal_m=float(dist.min()),closest_step=int(dist.argmin()),actual_walk_m=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()))
        if label!='V851':continue
        admissions=lines(cell/'model_admission.jsonl');assert len(admissions)==1200
        certs={}
        for folder in ['recovery_contracts','handover_certificates','progress_certificates']:
            for path in(cell/folder).glob('*.gz'):
                c=read(path);certs[c['created_step']]=c
        def split(a,b):
            groups={}
            for row in admissions[a:b]:
                step=row['step'];before=xy[step-1];after=xy[step];gain=float(np.linalg.norm(before-goal)-np.linalg.norm(after-goal))
                if row['status']=='RETAINED_REVERSE_BRAKE_CONTRACT':key='BACKUP_'+certs[row['retained_from_step']]['recovery_kind']
                else:key=('RETURN'if row.get('certified_backup_handover')else'ORDINARY')+'_GEAR_'+str(row.get('active_gear'))
                g=groups.setdefault(key,dict(steps=0,net_goal_gain_m=0.,walk_m=0.,negative_goal_steps=0));g['steps']+=1;g['net_goal_gain_m']+=gain;g['walk_m']+=float(np.linalg.norm(after-before));g['negative_goal_steps']+=gain<0
            assert sum(g['steps']for g in groups.values())==b-a
            assert abs(sum(g['net_goal_gain_m']for g in groups.values())-(dist[a-1]-dist[b-1]))<=1e-10
            return groups
        splits={f'{a}:{b}':split(a,b)for a,b in [(303,1200),(600,900),(900,1200)]}
        windows=[]
        for a,b in [(303,600),(600,900),(900,1200),(1100,1200)]:
            before=xy[a-1];walk=float(np.linalg.norm(np.diff(np.vstack((before,xy[a:b])),axis=0),axis=1).sum());windows.append(dict(start=a,end_exclusive=b,goal_before_m=float(dist[a-1]),goal_after_m=float(dist[b-1]),net_goal_gain_m=float(dist[a-1]-dist[b-1]),walk_m=walk))
        entered=np.flatnonzero(dist<=2.);first=int(entered[0]);assert first==1160
        plans=[read(p)for p in sorted(cell.glob('planning_*.json'))];complete=sum(p['stats']['status']=='GLOBAL_GOAL_PATH'for p in plans)
        details=dict(actual_mode_groups=splits,windows=windows,first_within2m_public_step=first,remaining_public_after_first_within2m=1200-(first+1),complete_goal_references=complete,total_reference_plans=len(plans),latency={k:v for k,v in read(cell/'CONTROL_LATENCY.json').items()if k!='records'})
    old,new=comparison['V848'],comparison['V851'];changes=dict(wall_time_change_percent=100*(new['elapsed_s']/old['elapsed_s']-1),private_native_change_percent=100*(new['prediction_steps']/old['prediction_steps']-1),new_planning_wall_fraction=new['planning_wall_s']/new['elapsed_s'])
    result=dict(status='SAVED_WALL_TIME_AND_ACTUAL_MODE_DECOMPOSITION_VERIFIED',comparison=comparison,changes=changes,details=details,new_models=0,new_integrations=0,training_updates=0,new_control_or_counterfactual_search=False,limitations='Actual logged-mode contribution is descriptive; no counterfactual claim that deleting reverse or increasing horizon would succeed. World clock pauses during computation; no realtime qualification.')
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');(out/'INPUT_SHA256.json').write_text(json.dumps(sources,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],comparison=comparison,changes=changes,first_within2m_public_step=first,remaining_public=1200-first-1,new_models=0,new_integrations=0)),flush=True)


if __name__=='__main__':main()
