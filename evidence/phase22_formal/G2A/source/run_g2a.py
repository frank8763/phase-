from __future__ import annotations

import argparse, csv, hashlib, inspect, json, math, os, random, signal, subprocess, sys, time
from pathlib import Path
import numpy as np
import torch
from stable_baselines3 import SAC

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'experiments/phase_paper_stageG2A_randomized_unknown_generalization_80_v1/results'
WORK = OUT / 'workers'
OUT.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)

MODEL = ROOT / 'training/phase20_unknown_obstacle_adaptation/checkpoints/stage_b_randomized/phase20_stage_b_325000_steps.zip'
MODEL_SHA = '4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f'
EVAL_MOD = 'training.phase21_risk_switch_fusion_sac.tests.eval_phase21_v3_exact_pair_5ep'
BASE_MOD, BASE_CLS = 'envs.phase21.mkmini_phase21_v11_candidate_recovery_env', 'MkMiniPhase21V11CandidateRecoveryEnv'
PROP_MOD, PROP_CLS = 'envs.phase22.mkmini_phase22_v1_continuous_corridor_env', 'MkMiniPhase22V1ContinuousCorridorEnv'
SEEDS = list(range(23100, 23180))
MAX_STEPS = 600
METHOD_WALL = 120
PAIR_WALL = 275
BOOT_N = 20000
PROTO = 'G2A_RANDOM_UNKNOWN_80_V1_20260915'

PREREG = {
    'protocol_version': PROTO,
    'purpose': 'randomized unknown-configuration generalization',
    'model_sha256': MODEL_SHA,
    'baseline': BASE_CLS,
    'proposed': PROP_CLS,
    'seeds': [23100, 23179],
    'n_pairs': 80,
    'randomized': True,
    'terminate_on_collision': True,
    'penetration_margin': 0.02,
    'safe_clearance': 0.35,
    'max_steps': 600,
    'success_dist_m': 0.90,
    'wall_timeout_per_method_s': 120,
    'control_domain_randomization': False,
    'final_holdout_22800_23099_reused': False,
    'method_tuning_after_open': False,
    'primary_endpoint': 'collision-free task success',
    'statistics': ['Wilson95', 'paired bootstrap20k', 'exact McNemar'],
}

class WallTimeout(Exception): pass

def alarm_handler(signum, frame): raise WallTimeout('method wall timeout')

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def safe(v):
    if isinstance(v,np.ndarray): return v.tolist()
    if isinstance(v,np.generic): return v.item()
    if isinstance(v,float): return v if math.isfinite(v) else None
    if isinstance(v,dict): return {str(k):safe(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [safe(x) for x in v]
    if isinstance(v,(str,int,bool)) or v is None: return v
    return repr(v)

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(safe(obj),ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8')
    tmp.replace(path)

def seed_all(seed):
    random.seed(seed); np.random.seed(seed & 0xffffffff); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)

def load_eval():
    import importlib
    E=importlib.import_module(EVAL_MOD)
    req=['synchronize_rngs','reset_env','scenario_signature','rollout']
    missing=[x for x in req if not callable(getattr(E,x,None))]
    if missing: raise RuntimeError('EXACT_EVAL_MISSING='+repr(missing))
    p=Path(inspect.getfile(E)).resolve()
    source=inspect.getsource(E.rollout)
    low=source.lower()
    evidence=[t for t in ('collision','robot_obstacle_contact','check_map_penetration','robot_sample_points','map_penetration') if t in low]
    if not evidence: raise RuntimeError('NO_COLLISION_PROTOCOL_EVIDENCE_IN_EXACT_ROLLOUT')
    if getattr(E,'MAX_STEPS',MAX_STEPS) != MAX_STEPS: raise RuntimeError('MAX_STEPS_PROTOCOL_MISMATCH')
    return E, {'path':str(p),'sha256':sha256(p),'rollout_signature':str(inspect.signature(E.rollout)),'collision_evidence':evidence}

def env_class(modname,clsname):
    import importlib
    return getattr(importlib.import_module(modname),clsname)

def prepare(E, cls, seed):
    seed_all(seed)
    env=cls(randomized=True, random_seed=seed, terminate_on_collision=True, penetration_margin=0.02, safe_clearance=0.35)
    if hasattr(env,'phase17_enable_domain_randomization'): env.phase17_enable_domain_randomization=False
    E.synchronize_rngs(env,seed)
    obs,info=E.reset_env(env,seed)
    obs=np.asarray(obs,dtype=np.float32)
    if obs.shape != (186,): raise RuntimeError('OBS_SHAPE='+repr(obs.shape))
    return env,obs,dict(info or {}),safe(E.scenario_signature(env))

def normalize(result, wall):
    r=dict(result or {})
    success=bool(r.get('success',False)); collision=bool(r.get('collision',False)); timeout=bool(r.get('timeout',False))
    r=safe(r)
    r.update({'success':success,'collision':collision,'env_timeout':timeout,'wall_timeout':False,'safe_success':bool(success and not collision),'wall_seconds':float(wall)})
    r['final_class']='COLLISION' if collision else ('SAFE_SUCCESS' if success else ('ENV_TIMEOUT' if timeout else 'OTHER_FAILURE'))
    return r

def run_method(E, env, obs, info, model, method):
    signal.signal(signal.SIGALRM,alarm_handler); signal.alarm(METHOD_WALL)
    t=time.perf_counter()
    try:
        row=normalize(E.rollout(env,obs,info,model),time.perf_counter()-t)
    except WallTimeout:
        row={'success':False,'collision':False,'env_timeout':False,'wall_timeout':True,'safe_success':False,'wall_seconds':time.perf_counter()-t,'final_class':'WALL_TIMEOUT'}
    finally: signal.alarm(0)
    if method=='proposed':
        for dst,src,default in [
            ('phase22_attempted','phase22_v1_attempted',False),('phase22_corridor_success','phase22_v1_success',False),
            ('phase22_candidate_count','phase22_v1_candidate_count',0),('phase22_failure_reason','phase22_v1_failure_reason','none'),
            ('phase22_selected_known_margin','phase22_v1_selected_known_margin',float('nan')),
            ('phase22_selected_sensor_margin','phase22_v1_selected_sensor_margin',float('nan')),
            ('phase22_selected_p95_curvature','phase22_v1_selected_p95_curvature',float('nan')),
            ('phase22_selected_heading_delta','phase22_v1_selected_heading_delta',float('nan')),
            ('phase22_reverse_count','phase22_v1_reverse_count',0)]: row[dst]=safe(getattr(env,src,default))
    return row

def pair_worker(seed):
    if seed not in SEEDS: raise RuntimeError('SEED_OUTSIDE_PREREG')
    if sha256(MODEL)!=MODEL_SHA: raise RuntimeError('MODEL_SHA_MISMATCH')
    E,pinfo=load_eval(); BC=env_class(BASE_MOD,BASE_CLS); PC=env_class(PROP_MOD,PROP_CLS)
    be=pe=None
    try:
        be,bo,bi,bs=prepare(E,BC,seed); pe,po,pi,ps=prepare(E,PC,seed)
        same=(bs==ps)
        dump(WORK/f'scenario_{seed}.json',{'protocol_version':PROTO,'seed':seed,'same_scenario':same,'baseline':bs,'proposed':ps})
        if not same:
            dump(WORK/f'pair_{seed}.json',{'protocol_version':PROTO,'seed':seed,'same_scenario':False,'protocol_failure':'SCENARIO_MISMATCH'})
            print('SCENARIO_MISMATCH',seed,flush=True); return 4
        model=SAC.load(str(MODEL),device='cpu')
        br=run_method(E,be,bo,bi,model,'baseline'); pr=run_method(E,pe,po,pi,model,'proposed')
        row={'protocol_version':PROTO,'seed':seed,'same_scenario':True,'scenario_signature':bs,'baseline':br,'proposed':pr,'protocol_info':pinfo}
        dump(WORK/f'pair_{seed}.json',row)
        print('PAIR_DONE',seed,'base='+br['final_class'],'prop='+pr['final_class'],'phase22='+str(pr.get('phase22_attempted',False)),flush=True)
        return 0
    finally:
        for e in (be,pe):
            if e is not None:
                try:e.close()
                except Exception:pass

def protocol_probe():
    if not MODEL.is_file() or sha256(MODEL)!=MODEL_SHA: raise RuntimeError('MODEL_SHA_MISMATCH')
    E,pinfo=load_eval(); BC=env_class(BASE_MOD,BASE_CLS); PC=env_class(PROP_MOD,PROP_CLS)
    be=pe=None
    try:
        be,_,_,bs=prepare(E,BC,SEEDS[0]); pe,_,_,ps=prepare(E,PC,SEEDS[0]); same=(bs==ps)
        cfg={k:bs.get(k) for k in ('unknown_radius','unknown_lateral_offset','unknown_path_fraction','endpoint_clearance')}
        row={'protocol_version':PROTO,'seed':SEEDS[0],'same_scenario':same,'config':cfg,'scenario_signature':bs,'protocol_info':pinfo,'NO_ROLLOUT_PERFORMED':True}
        dump(OUT/'protocol_probe.json',row)
        print('MODEL_SHA_MATCH=True'); print('PROBE_SEED='+str(SEEDS[0])); print('SAME_SCENARIO='+str(same)); print('RANDOMIZED_CONFIG='+repr(cfg)); print('NO_ROLLOUT_PERFORMED=TRUE')
        print('COLLISION_PROTOCOL_EVIDENCE='+','.join(pinfo['collision_evidence']))
        ok=same and all(v is not None for v in cfg.values())
        print('G2A_PROTOCOL_PROBE='+('PASS' if ok else 'FAIL'))
        return 0 if ok else 5
    finally:
        for e in (be,pe):
            if e is not None:
                try:e.close()
                except Exception:pass

def wilson(k,n,z=1.959963984540054):
    if n==0:return [None,None]
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0,c-h),min(1,c+h)]

def mcnemar(b,c):
    n=b+c
    if n==0:return 1.0
    k=min(b,c); return min(1.0,2.0*sum(math.comb(n,i) for i in range(k+1))/(2**n))

def bootstrap(base,prop):
    d=prop.astype(float)-base.astype(float); n=len(d)
    if not n:return {'diff':None,'ci95':[None,None],'n_boot':BOOT_N}
    rng=np.random.default_rng(20260915); x=np.empty(BOOT_N)
    for i in range(BOOT_N): x[i]=np.mean(d[rng.integers(0,n,n)])
    return {'diff':float(np.mean(d)),'ci95':[float(np.quantile(x,.025)),float(np.quantile(x,.975))],'n_boot':BOOT_N}

def bin_summary(rows,method,key):
    x=[bool(r[method].get(key,False)) for r in rows]; k=sum(x); n=len(x)
    return {'count':int(k),'n':n,'rate':k/n if n else None,'wilson95':wilson(k,n)}

def coverage(rows):
    fs=('unknown_radius','unknown_lateral_offset','unknown_path_fraction','endpoint_clearance'); fields={}
    for f in fs:
        a=np.array([float(r['scenario_signature'][f]) for r in rows])
        fields[f]={'min':float(a.min()),'max':float(a.max()),'mean':float(a.mean()),'std':float(a.std()),'unique':int(len(np.unique(a)))}
    return {'fields':fields,'unique_config_tuples':len({tuple(r['scenario_signature'][f] for f in fs) for r in rows}),
            'unique_starts':len({tuple(r['scenario_signature'].get('robot_xy') or []) for r in rows}),
            'unique_goals':len({tuple(r['scenario_signature'].get('goal_xy') or []) for r in rows}),
            'unique_paths':len({r['scenario_signature'].get('original_path_hash') for r in rows}),
            'unique_unknown_geometries':len({r['scenario_signature'].get('unknown_hash') for r in rows})}

def summarize(rows):
    n=len(rows); bs=np.array([bool(r['baseline'].get('safe_success')) for r in rows]); ps=np.array([bool(r['proposed'].get('safe_success')) for r in rows])
    bc=np.array([bool(r['baseline'].get('collision')) for r in rows]); pc=np.array([bool(r['proposed'].get('collision')) for r in rows])
    po=int(np.sum(ps & ~bs)); bo=int(np.sum(bs & ~ps)); pco=int(np.sum(pc & ~bc)); bco=int(np.sum(bc & ~pc))
    return {'n_pairs':n,'scenario_mismatch_count':sum(not r.get('same_scenario',False) for r in rows),
      'baseline':{'safe_success':bin_summary(rows,'baseline','safe_success'),'collision':bin_summary(rows,'baseline','collision'),'env_timeout':bin_summary(rows,'baseline','env_timeout'),'wall_timeout':bin_summary(rows,'baseline','wall_timeout'),'mean_wall_s':float(np.mean([r['baseline']['wall_seconds'] for r in rows])) if n else None},
      'proposed':{'safe_success':bin_summary(rows,'proposed','safe_success'),'collision':bin_summary(rows,'proposed','collision'),'env_timeout':bin_summary(rows,'proposed','env_timeout'),'wall_timeout':bin_summary(rows,'proposed','wall_timeout'),'mean_wall_s':float(np.mean([r['proposed']['wall_seconds'] for r in rows])) if n else None,'phase22_attempted':sum(bool(r['proposed'].get('phase22_attempted')) for r in rows),'phase22_corridor_success':sum(bool(r['proposed'].get('phase22_corridor_success')) for r in rows)},
      'paired_safe_success':{'proposed_only':po,'baseline_only':bo,'both':int(np.sum(ps&bs)),'neither':int(np.sum(~ps&~bs)),'difference':float(np.mean(ps)-np.mean(bs)) if n else None,'bootstrap':bootstrap(bs,ps),'mcnemar_p':mcnemar(po,bo)},
      'paired_collision':{'proposed_only':pco,'baseline_only':bco,'both':int(np.sum(pc&bc)),'neither':int(np.sum(~pc&~bc)),'difference':float(np.mean(pc)-np.mean(bc)) if n else None,'mcnemar_p':mcnemar(pco,bco)},
      'coverage':coverage(rows) if n else None}

def write_csv(rows):
    path=OUT/'g2a_pairs.csv'; names=['seed','unknown_radius','unknown_lateral_offset','unknown_path_fraction','endpoint_clearance','base_safe','base_collision','base_wall_timeout','prop_safe','prop_collision','prop_wall_timeout','phase22_attempted','phase22_corridor_success','phase22_candidate_count']
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=names); w.writeheader()
        for r in rows:
            s,b,p=r['scenario_signature'],r['baseline'],r['proposed']; w.writerow({'seed':r['seed'],'unknown_radius':s.get('unknown_radius'),'unknown_lateral_offset':s.get('unknown_lateral_offset'),'unknown_path_fraction':s.get('unknown_path_fraction'),'endpoint_clearance':s.get('endpoint_clearance'),'base_safe':b.get('safe_success'),'base_collision':b.get('collision'),'base_wall_timeout':b.get('wall_timeout'),'prop_safe':p.get('safe_success'),'prop_collision':p.get('collision'),'prop_wall_timeout':p.get('wall_timeout'),'phase22_attempted':p.get('phase22_attempted'),'phase22_corridor_success':p.get('phase22_corridor_success'),'phase22_candidate_count':p.get('phase22_candidate_count')})
    return path

def formal():
    if sha256(MODEL)!=MODEL_SHA: raise RuntimeError('MODEL_SHA_MISMATCH')
    probe=OUT/'protocol_probe.json'
    if not probe.is_file() or not json.loads(probe.read_text())['same_scenario']: raise RuntimeError('RUN_PROTOCOL_PROBE_FIRST')
    dump(OUT/'preregistration.json',PREREG)
    print('='*88); print('G2A RANDOMIZED UNKNOWN-CONFIG GENERALIZATION — 80 FRESH PAIRED SEEDS'); print('='*88)
    print('SEEDS=23100..23179'); print('FINAL_HOLDOUT_22800_23099_USED=FALSE'); print('NO_TUNING_AFTER_OPEN=TRUE'); print('PAPER_RUNTIME_ACCELERATORS=DISABLED')
    script=Path(__file__).resolve(); rows=[]; failures=[]
    for i,seed in enumerate(SEEDS,1):
        p=WORK/f'pair_{seed}.json'
        if p.is_file():
            try:
                old=json.loads(p.read_text())
                if old.get('protocol_version')==PROTO and old.get('same_scenario') and 'baseline' in old and 'proposed' in old:
                    rows.append(old); print(f'RESUME {i}/80 seed={seed}'); continue
            except Exception: pass
        print(f'PAIR_START {i}/80 seed={seed}',flush=True)
        try:
            q=subprocess.run([sys.executable,'-u',str(script),'--pair-worker','--seed',str(seed)],cwd=str(ROOT),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=PAIR_WALL,env=dict(os.environ))
            print(q.stdout,end='')
            if q.returncode!=0: failures.append({'seed':seed,'rc':q.returncode,'tail':q.stdout[-3000:]}); continue
        except subprocess.TimeoutExpired as e:
            failures.append({'seed':seed,'rc':124,'tail':str(e.stdout or '')[-3000:]}); print('PAIR_HARD_TIMEOUT',seed); continue
        if not p.is_file(): failures.append({'seed':seed,'rc':98,'tail':'missing pair json'}); continue
        r=json.loads(p.read_text())
        if not r.get('same_scenario'):
            failures.append({'seed':seed,'rc':97,'tail':'scenario mismatch'}); print('FORMAL_ABORT_SCENARIO_MISMATCH'); break
        rows.append(r); sm=summarize(rows); dump(OUT/'progress.json',{'completed':len(rows),'target':80,'failures':failures,'summary':sm})
        print('PROGRESS',len(rows),'/80','base_safe',sm['baseline']['safe_success']['count'],'prop_safe',sm['proposed']['safe_success']['count'],flush=True)
    rows=sorted(rows,key=lambda x:x['seed']); sm=summarize(rows); csvp=write_csv(rows); complete=(len(rows)==80 and not failures and sm['scenario_mismatch_count']==0)
    report={'protocol_version':PROTO,'preregistration':PREREG,'formal_complete':complete,'completed_pairs':len(rows),'target_pairs':80,'protocol_failures':failures,'summary':sm,'rows':rows,'csv':str(csvp)}; rp=OUT/'g2a_final_report.json'; dump(rp,report)
    print('\n'+'='*88); print('G2A FINAL SUMMARY'); print('='*88); print('FORMAL_COMPLETE='+str(complete)); print(f'COMPLETED_PAIRS={len(rows)}/80'); print('SCENARIO_MISMATCH_COUNT='+str(sm['scenario_mismatch_count']))
    b,p,ps,pc=sm['baseline'],sm['proposed'],sm['paired_safe_success'],sm['paired_collision']
    print('BASELINE_SAFE_SUCCESS='+repr(b['safe_success'])); print('PROPOSED_SAFE_SUCCESS='+repr(p['safe_success'])); print('SAFE_SUCCESS_DIFF='+str(ps['difference'])); print('SAFE_SUCCESS_BOOTSTRAP95='+repr(ps['bootstrap']['ci95'])); print('SAFE_SUCCESS_MCNEMAR_P='+str(ps['mcnemar_p']))
    print('BASELINE_COLLISION='+repr(b['collision'])); print('PROPOSED_COLLISION='+repr(p['collision'])); print('COLLISION_DIFF='+str(pc['difference'])); print('COLLISION_MCNEMAR_P='+str(pc['mcnemar_p']))
    print('PHASE22_ATTEMPTED='+str(p['phase22_attempted'])); print('PHASE22_CORRIDOR_SUCCESS='+str(p['phase22_corridor_success']))
    if sm['coverage']:
        c=sm['coverage']; print('UNIQUE_CONFIG_TUPLES='+str(c['unique_config_tuples'])); print('UNIQUE_STARTS='+str(c['unique_starts'])); print('UNIQUE_GOALS='+str(c['unique_goals'])); print('UNIQUE_PATHS='+str(c['unique_paths'])); print('UNIQUE_UNKNOWN_GEOMETRIES='+str(c['unique_unknown_geometries'])); print('CONFIG_FIELDS='+repr(c['fields']))
    print('FINAL_REPORT='+str(rp)); print('CSV='+str(csvp)); print('G2A_RUN='+('PASS' if complete else 'INCOMPLETE_RESUME'))
    return 0 if complete else 2

def main():
    a=argparse.ArgumentParser(); a.add_argument('--protocol-probe',action='store_true'); a.add_argument('--pair-worker',action='store_true'); a.add_argument('--formal',action='store_true'); a.add_argument('--seed',type=int); x=a.parse_args()
    if x.protocol_probe:return protocol_probe()
    if x.pair_worker:return pair_worker(x.seed)
    if x.formal:return formal()
    raise RuntimeError('choose a mode')

if __name__=='__main__': raise SystemExit(main())
