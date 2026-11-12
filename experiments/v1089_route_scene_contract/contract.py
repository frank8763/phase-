"""Strict route-aware construction contract; geometry is never planner input."""
import json, hashlib, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent
SPEC=json.loads((C/'SCENE_CONTRACT.json').read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normalize_xml(text, anchor):
 root=ET.fromstring(text);nodes=root.findall(".//body[@name='phase_dynamic_actor']");assert len(nodes)==1,'ACTOR_STRUCTURE'
 actor=nodes[0];assert actor.attrib['mocap']=='true','ACTOR_NOT_MOCAP'
 assert np.array_equal(np.asarray(actor.attrib['pos'].split(),float),np.r_[anchor,0.]),'UNDECLARED_ACTOR_ANCHOR'
 actor.set('pos','REGISTERED_ROUTE_ANCHOR')
 return ET.tostring(root)
def verify_saved(ph,task,require_live=True):
 ph=Path(ph);setup=json.loads((ph/'SETUP.json').read_text());case=SPEC['routes'][task['case_id']];baseline=SPEC['baseline_contract'];build=json.loads((ph/'MODEL_BUILD_CONTRACT.json').read_text())
 assert setup['model_sha256']==digest(ph/'scene_model.mjb'),'MJB_BYTE_BINDING'
 assert setup['case']==case['case'] and setup['seed']==task['seed'] and setup['dynamic'] is True,'CASE_BINDING'
 for key in ['start_xy','goal_xy']:assert task[key]==case['case'][key]
 assert task['start_yaw']==case['case']['yaw']
 actor=setup['actor'];assert actor['case_id']==task['case_id']and actor['anchor_xy']==case['anchor_xy']and actor['axis_xy']==case['axis_xy'],'DECLARED_ACTOR_BINDING'
 assert actor['radius_m']==.1 and actor['amplitude_m']==.25 and actor['omega_rad_s']==.32 and actor['phase_rad']==task['phase'],'ACTOR_MOTION_CONTRACT'
 assert normalize_xml((ph/'PATCHED_ASSEMBLY.xml').read_text(),case['anchor_xy'])==normalize_xml(SPEC['baseline_assembly_xml'],SPEC['routes']['NORTH_SOUTH']['anchor_xy']),'VEHICLE_OR_STATIC_XML_CHANGED'
 a={r['name']:r for r in baseline['preserved_arrays']};b={r['name']:r for r in build['preserved_arrays']};assert a.keys()==b.keys()
 for name in a:
  if name not in {'body_pos','light_poscom0'}:assert a[name]==b[name],'COMPILED_ARRAY_CHANGED '+name
  else:assert a[name]['shape']==b[name]['shape']and a[name]['dtype']==b[name]['dtype']
 for name in ['interface','permitted_structural_shape_changes','exclude_signatures','preserved_option_fields']:assert build[name]==baseline[name],'BUILD_CONTRACT_CHANGED '+name
 assert setup['dt']==.01 and setup['stage_isolated'] is True
 if task['case_id']=='NORTH_SOUTH':assert setup['model_sha256']==SPEC['baseline_NS_sha'],'NS_MODEL_CHANGED'
 if task['case_id']=='WEST_EAST':assert setup['model_sha256']==SPEC['known_WE_sha'],'WE_MODEL_CHANGED'
 proof=ph/'SCENE_MODEL_CONTRACT.json'
 assert proof.exists()or not require_live,'LIVE_MODEL_CONTRACT_MISSING'
 if proof.exists():
  p=json.loads(proof.read_text());assert p['passed']and p['live_model_arrays_verified']and p['model_sha256']==setup['model_sha256'];assert p['normalized_body_pos_sha256']==a['body_pos']['sha256']
 return dict(passed=True,model_sha256=setup['model_sha256'],declared_route=task['case_id'],compiled_arrays=len(a),same_nonderived_arrays=len(a)-2,registered_actor_anchor=case['anchor_xy'])
def verify_live(v,task):
 ph=v.out;assert v.count==0 and v.d.time==0.
 answer=verify_saved(ph,task,require_live=False);build=json.loads((ph/'MODEL_BUILD_CONTRACT.json').read_text())
 for row in build['preserved_arrays']:
  array=np.asarray(getattr(v.m,row['name']));assert list(array.shape)==row['shape']and str(array.dtype)==row['dtype']and hashlib.sha256(array.tobytes()).hexdigest()==row['sha256'],'LIVE_ARRAY_MISMATCH '+row['name']
 pos=np.asarray(v.m.body_pos).copy();idx=v.m.body('phase_dynamic_actor').id;assert np.array_equal(pos[idx],np.r_[SPEC['routes'][task['case_id']]['anchor_xy'],0.]);pos[idx]=np.r_[SPEC['routes']['NORTH_SOUTH']['anchor_xy'],0.]
 expected=next(r['sha256']for r in SPEC['baseline_contract']['preserved_arrays']if r['name']=='body_pos');h=hashlib.sha256(pos.tobytes()).hexdigest();assert h==expected,'NONACTOR_BODY_POSITION_CHANGED'
 answer.update(live_model_arrays_verified=True,normalized_body_pos_sha256=h,models_initialized_here=0,native_integrations_here=0)
 (ph/'SCENE_MODEL_CONTRACT.json').write_text(json.dumps(answer,indent=2)+'\n');return answer
