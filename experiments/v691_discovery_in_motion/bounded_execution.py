"""Sequential isolated execution, immutable source snapshots and strict audits."""
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import numpy as np
from contact_fingerprint import compare_contacts


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Window:
    def __init__(self, src, root_name, window_name, limit_s, absolute_deadline):
        self.src = Path(src).resolve(); self.repo = self.src.parents[1]
        self.root = self.repo/'runs'/root_name; self.root.mkdir(exist_ok=True)
        self.lock = (self.root/'window.lock').open('a+')
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.path = self.root/window_name; self.path.mkdir()
        self.started = time.monotonic(); self.unix = time.time()
        self.limit = min(limit_s, absolute_deadline-self.unix)
        assert self.limit > 960
        self.sources = {p.name:digest(p) for p in sorted(self.src.glob('*.py'))}
        self.documents = {p.name:digest(p) for p in sorted(self.src.glob('*.md'))}
        self.ledger, self.physical = [], []
        dump(self.path/'WINDOW.json', {'started_unix':self.unix, 'limit_s':self.limit,
             'absolute_deadline_unix':self.unix+self.limit, 'overnight_absolute_deadline_unix':absolute_deadline,
             'pid':os.getpid(), 'single_cpu_sequential':True})
        dump(self.path/'SOURCE_FREEZE.json',self.sources)
        dump(self.path/'DOCUMENT_FREEZE.json',self.documents)
        for name in self.documents:
            (self.path/name).write_bytes((self.src/name).read_bytes())

    def remaining(self):
        return self.limit-(time.monotonic()-self.started)

    def frozen(self):
        assert all(digest(self.src/n)==h for n,h in self.sources.items()), 'SOURCE_CHANGED'
        assert all(digest(self.src/n)==h for n,h in self.documents.items()), 'PROTOCOL_CHANGED'

    def execute(self, command, log, seconds):
        assert self.remaining() > seconds+3, 'INSUFFICIENT_PROCESS_BUDGET'
        with log.open('w') as stream:
            process = subprocess.Popen(command,cwd=self.repo,stdout=stream,stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                return process.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGTERM)
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL); process.wait()
                return 124
            except BaseException:
                if process.poll() is None:
                    os.killpg(process.pid,signal.SIGTERM)
                    try: process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid,signal.SIGKILL); process.wait()
                raise

    def run(self, name, seed, scene, feasibility=False, mode="predictive", observation_steps=32):
        self.frozen()
        if self.remaining() < (55 if feasibility else 1000):
            return None
        dump(self.path/'ACTIVE.json', {'name':name,'seed':seed,'scene':scene,
             'feasibility_only':feasibility,'started_unix':time.time()})
        command = [str(self.repo/'run_phase.sh'),str(self.src.relative_to(self.repo)/'run_static.py'),
                   '--name',name,'--seed',str(seed),'--scene',scene,'--conditions','geometry_memory',
                   '--wall-seconds',str(40 if feasibility else 900),'--max-steps','1200']
        command += ['--dynamic-mode',mode,'--initial-observation-steps',str(observation_steps)]
        if feasibility: command.append('--feasibility-only')
        started = time.monotonic()
        code = self.execute(command,self.path/(name+'.console'),45 if feasibility else 905)
        pair = self.root/name/'paired'
        row = {'name':name,'seed':seed,'scene':scene,'feasibility_only':feasibility,
               'returncode':code,'wall_s':time.monotonic()-started,'completion':read(pair/'completion.json'),
               'preflight':read(pair/'PREFLIGHT.json'),'feasibility':read(pair/'TASK_FEASIBILITY.json'),
               'protocol':read(pair/'STATIC_PROTOCOL.json'),'interrupted':read(pair/'geometry_memory/interrupted.json'),
               'run_root':str(self.root.relative_to(self.repo)),'initial_observation_steps':observation_steps}
        self.ledger.append(row); dump(self.path/'LEDGER.json',self.ledger)
        dump(self.path/'ACTIVE.json',{'status':'AUDIT_OR_NEXT','last_completed':name})
        print(name,'code',code,'remaining_s',round(self.remaining(),1),flush=True)
        return row

    def result(self, row):
        values = ((row or {}).get('completion') or {}).get('results',[])
        return values[0] if values else None

    def audit(self, row):
        result = self.result(row)
        if result is None:
            return False
        self.frozen(); pair = self.root/row['name']/'paired'
        code = self.execute([str(self.repo/'run_phase.sh'),str(self.src.relative_to(self.repo)/'replay_native_audit.py'),str(pair)],
                            pair/'native_replay.console',35)
        integrity = self.execute(['python',str(self.repo/'experiments/v648_static_unknown/audit_results.py'),str(pair)],
                                 pair/'integrity.console',15)
        native = read(pair/'NATIVE_REPLAY_AUDIT.json',{})
        cell = pair/'geometry_memory'
        admissions = [json.loads(s) for s in (cell/'model_admission.jsonl').read_text().splitlines()]
        plans = {int(p.stem.split('_')[-1]) for p in cell.glob('planning_*.json')}
        switch_file = cell/'gear_transitions.jsonl'
        switches = {json.loads(s)['step'] for s in switch_file.read_text().splitlines()} if switch_file.exists() else set()
        bypasses = [b['step'] for a,b in zip(admissions[:-1],admissions[1:])
                    if a['active_gear']!=b['active_gear'] and b['step']not in plans and b['step']not in switches]
        checks = {'replay_exit':code==0, 'integrity':integrity==0,
                  'frozen_snapshot':read(pair.parent/'source_snapshot/SHA256.json')==self.sources,
                  'model':digest(pair/'scene_model.mjb')==row['protocol']['full_model_sha256']==native.get('scene_model_sha256'),
                  'replay_match':native.get('status')=='MATCHED_RECORDED_PUBLIC_STATES'
                      and native['maximum_full_public_qpos_error']<=1e-8 and native['maximum_full_public_qvel_error']<=1e-8,
                  'native_count':native.get('replay_integration_steps')==result['physics_steps']==8*result['public_steps'],
                  'native_clearance':native.get('minimum_reconstructed_native_actual_axis_AABB_clearance_m',-1)>=.15-1e-8
                      and native.get('reconstructed_native_states_below_015')==0,
                  'zero_contacts':native.get('replay_obstacle_contact_records')==0 and all(result['contacts'][k]==0
                      for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records']),
                  'complete_self_domain':result['minimum_actual_self_domain_margin_m']>=0
                      and result['self_geometry_checked_native_ticks']==result['physics_steps']
                      and native.get('minimum_reconstructed_self_domain_margin_m',-1)>=0,
                  'static_obstacles':result['static_obstacle_pose_unchanged'],
                  'native_only':result['root_mutations_outside_mjstep']==0,
                  'causal_admission':len(admissions)==result['public_steps'] and all(x['hidden_world_geometry_used']is False for x in admissions),
                  'stopped_cusps':not bypasses}
        record = {'name':row['name'],'passed':all(checks.values()),'checks':checks,'replay':native}
        self.physical.append(record); dump(self.root/'FINAL_PHYSICAL_AUDITS.json',self.physical)
        return record['passed']

    def repeat(self, row, base):
        result = self.result(row); safe = self.audit(row)
        pair = self.root/row['name']/'paired'
        old = read(base/'geometry_memory/result.json')
        a = [json.loads(s) for s in (base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
        b = [json.loads(s) for s in (pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
        errors = {k:float(np.max(np.abs(np.asarray([x[k]for x in a])-np.asarray([x[k]for x in b]))))
                  if len(a)==len(b) and a else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']}
        contact = compare_contacts(base,pair) if result else {'passed':False}
        checks = {'physical_audit':safe,'full_state_and_control':all(v is not None and v<=1e-8 for v in errors.values()),
                  'same_model':read(base/'STATIC_PROTOCOL.json')['full_model_sha256']==read(pair/'STATIC_PROTOCOL.json')['full_model_sha256'],
                  'same_normalized_initial_state':bool(result and result['normalized_initial_state_hash']==old['normalized_initial_state_hash']),
                  'exact_contact_events_except_verified_xml_provenance':contact['passed'],
                  'same_strict_goal':bool(result and result['strict_safe_arrival'] and result['outcome']==old['outcome']=='GOAL')}
        record = {'name':row['name'],'seed':row['seed'],'scene':row['scene'],'matched':all(checks.values()),
                  'checks':checks,'full_public_maximum_errors':errors,'original_public_steps':len(a),
                  'repeat_public_steps':len(b),'contact_comparison':contact}
        dump(pair/'EXACT_REPEAT_AUDIT.json',record)
        return record
