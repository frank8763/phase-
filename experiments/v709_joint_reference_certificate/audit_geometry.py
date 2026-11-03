"""Independent scalar geometry, including reused and new scene provenance."""
import hashlib,importlib.util,json,math,sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'runs/v709_joint_reference_certificate'
spec=importlib.util.spec_from_file_location('v708_independent_scalar_geometry',REPO/'experiments/v708_joint_field_qualification/audit_geometry.py')
scalar=importlib.util.module_from_spec(spec);spec.loader.exec_module(scalar)
placement,continuous=scalar.placement,scalar.continuous
read=lambda p:json.loads(p.read_text())
known=read(REPO/'experiments/v706_global_field_qualification/KNOWN_FIELD.json');cases=read(REPO/'experiments/v706_global_field_qualification/SCENE_CASES.json');details=[]
for case in cases:
 p=ROOT/case['id']/'RESULT.json'
 if not p.exists() or not read(p)['eligible']:
  details.append(dict(case_id=case['id'],passed=False,checks=dict(constructor_eligible=False)));continue
 result=read(p);selection=result['selection'];anchor=selection['anchor_xy'];cert=selection['certificate'];path=cert['reference_path'];lower=continuous(path,known,anchor)
 checks=placement(anchor,case,known,selection['swept_radius_m'])
 checks.update(continuous_reference=lower>=.15-1e-12,recorded_bound_matches=abs(lower-cert['continuous_polygonal_pose_clearance_lower_bound_m'])<=1e-10,
  exact_start=path[0][:3]==[*case['start_xy'],case['yaw']],goal_distance=math.dist(path[-1][:2],case['goal_xy'])<=.28)
 if result.get('source'):
  checks['reused_certified_geometry_exact']=selection==read(REPO/result['source'])['selection']
 else:
  candidates=read(ROOT/case['id']/'CANDIDATE_GRID.json')['candidates'];rank=selection['rank'];first=next((i for i,x in enumerate(candidates) if x['eligible']),None)
  checks['first_geometric_certificate']=first==rank and candidates[rank]['anchor_xy']==anchor
  checks['nearby_course_scope']=selection['nearest_reference_distance_m']<=1.50
  checks['unmodified_known_reference']=path==read(ROOT/case['id']/'KNOWN_REFERENCE_CERTIFICATE.json')['reference_path']
 negative=dict(start_anchor_rejected=not all(placement(case['start_xy'],case,known).values()),shrunken_sweep_rejected=not all(placement(anchor,case,known,.20).values()))
 details.append(dict(case_id=case['id'],checks=checks,negative_controls=negative,anchor_xy=anchor,continuous_lower_bound_m=lower,passed=all(checks.values())and all(negative.values())))
freeze=read(Path(__file__).parent/'SOURCE_FREEZE.json');completion=read(ROOT/'COMPLETION.json')
checks=dict(all_three=len(details)==3 and all(x['passed'] for x in details),frozen_inputs=all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items()),zero_integration=all(completion[k]==0 for k in ['initializations','navigation_integrations','private_integrations','replay_integrations','training_updates']) and not completion['simulator_imported'])
out=dict(status='ALL_THREE_JOINT_GEOMETRY_INDEPENDENTLY_VERIFIED' if all(checks.values())else'JOINT_GEOMETRY_AUDIT_NOT_PASSED',checks=checks,details=details,verification_integrations=0,
 scope='Two V708 swept-detour witnesses and a nearby nonblocking north-south actor; physical discovery, braking and arrival untested. The north-south actor does not necessarily obstruct the known reference.')
(ROOT/'INDEPENDENT_GEOMETRY_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));raise SystemExit(0 if all(checks.values())else 1)
