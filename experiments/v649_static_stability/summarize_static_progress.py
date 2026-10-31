"""Compact read-only progress for the active bounded static windows."""
import json
from pathlib import Path
repo = Path(__file__).resolve().parents[2]
dev = repo/'runs/v651_static_progress'
for run in sorted(dev.glob('dev*')):
    if not run.is_dir():
        continue
    pair = run/'paired'
    result = pair/'geometry_memory/result.json'
    if result.exists():
        j = json.loads(result.read_text())
        audit = pair/'DEVELOPMENT_AUDIT.json'
        print(run.name,j['outcome'],j['public_steps'],'goal',round(j['goal_distance_m'],3),'audit',json.loads(audit.read_text())['checks_passed'] if audit.exists() else 'pending')
    elif not (pair/'completion.json').exists():
        p = pair/'geometry_memory/partial_progress.json'
        print(run.name,'ACTIVE', {k:v for k,v in json.loads(p.read_text()).items() if k in ['public_steps','goal_distance_m','elapsed_s']} if p.exists() else 'initializing')
window = repo/'runs/v652_static_confirmation/confirmation_window01'
if window.exists():
    ledger = json.loads((window/'LEDGER.json').read_text()) if (window/'LEDGER.json').exists() else []
    preflight = [x for x in ledger if x['feasibility_only']]
    counts = {s:sum(x['scene'] == s and bool(x['feasibility'] and x['feasibility']['eligible']) for x in preflight) for s in ['single_event','legacy_two']}
    outcomes = json.loads((window/'CONFIRMATION_RESULTS.json').read_text()) if (window/'CONFIRMATION_RESULTS.json').exists() else []
    print('V652 screened',len(preflight),'eligible',counts,'completed',len(outcomes),'strict',sum(x['strict_success'] for x in outcomes))
    p = window/'ACTIVE.json'
    if p.exists():
        active = json.loads(p.read_text());print('V652 active',active)
        if active.get('name'):
            q = window.parent/active['name']/'paired/geometry_memory/partial_progress.json'
            if q.exists():
                j = json.loads(q.read_text());print('active progress',{k:j[k] for k in ['public_steps','goal_distance_m','elapsed_s']})
    if (window/'COMPLETION.json').exists():print('V652 completion',json.loads((window/'COMPLETION.json').read_text()))
continuation = repo/'runs/v653_static_log_recovery/continuation01'
if continuation.exists():
    p = continuation/'CONFIRMATION_RESULTS.json'
    rows = json.loads(p.read_text()) if p.exists() else []
    print('V653 same-list continuation attempts',len(rows),'strict',sum(x['strict_success'] for x in rows),'non_successes',sum(not x['strict_success'] for x in rows),'original interruption retained')
    if (continuation/'ACTIVE.json').exists():
        active=json.loads((continuation/'ACTIVE.json').read_text());print('V653 active',active)
        if active.get('name'):
            p=continuation.parent/active['name']/'paired/geometry_memory/partial_progress.json'
            if p.exists():
                j=json.loads(p.read_text());print('V653 progress',{k:j[k] for k in ['public_steps','goal_distance_m','elapsed_s']})
    if (continuation/'COMPLETION.json').exists():print('V653 completion',json.loads((continuation/'COMPLETION.json').read_text()))
