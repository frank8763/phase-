"""Read-only acceptance audit; never promotes a partial or screened result."""
import argparse,gzip,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('window');a=p.parse_args();window=Path(a.window);root=window.parent;selection=json.loads((window/'SELECTION_FREEZE.json').read_text());summary=json.loads((window/'COMPLETION.json').read_text());rows=json.loads((window/'CONFIRMATION_RESULTS.json').read_text())if(window/'CONFIRMATION_RESULTS.json').exists()else[];checks=[];all_safe=True
for r in rows:
    pair=root/r['name']/'paired';record=r['result']
    if record is None:checks.append({'name':r['name'],'completed':False,'strict_success':False});continue
    branch=pair/'geometry_memory';h=hashlib.sha256()
    with gzip.open(branch/'contacts.jsonl.gz','rb')as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    assert h.hexdigest()==record['contacts']['contact_log_content_sha256']
    trace=json.loads((branch/'trace.json').read_text());assert len(trace)==record['public_steps']and record['physics_steps']==8*len(trace)
    assert record['self_geometry_checked_native_ticks']==record['physics_steps']and record['minimum_actual_self_domain_margin_m']>=0
    assert record['root_mutations_outside_mjstep']==0 and record['static_obstacle_pose_unchanged']
    safe=all(record['contacts'][k]==0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records'])
    all_safe &= safe
    checks.append({'name':r['name'],'completed':True,'strict_success':r['strict_success'],'contact_digest_verified':True,'physics_steps':record['physics_steps'],'safe':safe,'scene_matches_preflight':r['scene_matches_preflight']})
counts={s:sum(r['strict_success']for r in rows if r['scene']==s)for s in ['single_event','legacy_two']}
navigation_gate=len(selection['tasks'])==24 and len(rows)==24 and sum(x['strict_success']for x in rows)>=23 and all(v>=11 for v in counts.values())and all_safe
out={'navigation_gate_met':navigation_gate,'static_acceptance_passed':False,'reason':'repeats and native-clearance replay audits additionally required'if navigation_gate else'new-scene navigation gate incomplete/failed','selected_tasks':len(selection['tasks']),'completed_attempts':len(rows),'strict_successes':sum(x['strict_success']for x in rows),'class_successes':counts,'checks':checks,'simulation_steps':0,'dynamic_started':False}
(window/'INTEGRITY_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
