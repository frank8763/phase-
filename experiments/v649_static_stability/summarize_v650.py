"""Read-only concise status of the separate V650 experiment window."""
import json,time
from collections import Counter
from pathlib import Path
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v650_static_acceptance'
for window in sorted(root.glob('acceptance_window*')):
    ledger=json.loads((window/'LEDGER.json').read_text())if(window/'LEDGER.json').exists()else[]
    screened=[x for x in ledger if x['feasibility_only']];nav=[x for x in ledger if not x['feasibility_only']]
    print(window.name,'screened',len(screened),'eligible',dict(Counter(x['scene']for x in screened if x['feasibility']and x['feasibility']['eligible'])),'navigation',len(nav))
    completion=window/'COMPLETION.json';active=window/'ACTIVE.json'
    if completion.exists():
        j=json.loads(completion.read_text());print('status',j['status'],'success',j['strict_arrivals'],'failed',j['confirmation_failures'])
    elif active.exists():
        j=json.loads(active.read_text());print('active',j.get('name',j.get('status')))
        if j.get('name'):
            p=root/j['name']/'paired/geometry_memory/partial_progress.json'
            if p.exists():
                progress=json.loads(p.read_text());print('partial',progress['public_steps'],round(progress['goal_distance_m'],3),'m',round(progress['elapsed_s'],1),'s')
