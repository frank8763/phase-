"""Offline resource and audit accounting; no controller or simulator execution."""
import json,gzip,subprocess,sys,hashlib
from pathlib import Path
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v648_static_unknown';measured=0.;checks=[];missing=[];completed=0
for f in sorted(root.rglob('completion.json')):
 d=json.loads(f.read_text());elapsed=d.get('elapsed_s')
 if isinstance(elapsed,(float,int)):measured+=elapsed
 else:missing.append(str(f.relative_to(root)))
 if d.get('status')!='COMPLETE' or not d.get('results'):continue
 completed+=1
 out=subprocess.run([sys.executable,str(Path(__file__).parent/'audit_results.py'),str(f.parent)],capture_output=True,text=True)
 if out.returncode:raise RuntimeError(out.stdout+out.stderr)
 checks.append({'run':str(f.parent.relative_to(root)),'pass':True,'detail':json.loads(out.stdout)})
for run,file in [('dynamics_probe_10','response.json'),('scene_probe_11','scene_geometry.json'),('offline_search_probe_16','probe.json'),('map_connectivity_probe_16','connectivity.json'),('truth_connectivity_probe_16','connectivity.json'),('brake_response_probe_21','response.json')]:
 f=root/run/'paired'/file
 if f.exists():measured+=json.loads(f.read_text()).get('elapsed_s',0.)
reservation=230. # 200 for interrupted19, 30 for initial diagnostic/startup timing.
freeze=json.loads((Path(__file__).parent/'DECISION_FREEZE.json').read_text());sources=freeze['online_source_sha256']
for name,expected in sources.items():
 assert hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()==expected,name
 for run in ['static_pilot_21_single_seed4','static_pilot_22_map_ablation_seed4']:
  assert hashlib.sha256((root/run/'source_snapshot'/name).read_bytes()).hexdigest()==expected,(run,name)
result={'measured_execution_wall_s':measured,'unmeasured_timing_entries':missing,'additional_budget_reservation_s':reservation,'accounted_wall_s':measured+reservation,'final_protocol_limit_s':4500,'within_accounted_budget':measured+reservation<=4500,'timing_scope':'process/diagnostic execution only; analysis, code preparation and verification excluded; initial diagnostic and startup missing exact timings, reservation is accounting rather than a measurement','completed_static_run_integrity_audits':completed,'frozen_decision_sources_match_across_21_22':len(sources),'sac_training_updates':0,'stage_visible_in_readonly_probe':json.loads((root/'readiness_20261031.json').read_text())['isolated_probe']['stage_visible']}
(root/'completed_branch_audits.json').write_text(json.dumps(checks,indent=2));(root/'round_accounting.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
