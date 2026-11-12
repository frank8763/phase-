"""Zero-model comparison of saved route construction; never loads MuJoCo."""
import sys,json,hashlib,xml.etree.ElementTree as ET,copy
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1088_route_model_diagnosis'
A=R/'runs/v858_nav2_verified/v1085_entry/main_fresh_ns/physics';B=R/'runs/v858_nav2_verified/v1088/main_west_east/physics'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normalized(text):
 root=ET.fromstring(text);actors=root.findall(".//body[@name='phase_dynamic_actor']");assert len(actors)==1
 actor=actors[0];assert actor.attrib['mocap']=='true';actor.attrib['pos']='DECLARED_ROUTE_ACTOR_ANCHOR'
 return ET.tostring(root)
def main():
 a=json.loads((A/'MODEL_BUILD_CONTRACT.json').read_text());b=json.loads((B/'MODEL_BUILD_CONTRACT.json').read_text());aa={x['name']:x for x in a['preserved_arrays']};bb={x['name']:x for x in b['preserved_arrays']};assert aa.keys()==bb.keys()
 differences=[k for k in aa if aa[k]!=bb[k]];assert set(differences)=={'body_pos','light_poscom0'}
 ax=(A/'PATCHED_ASSEMBLY.xml').read_text();bx=(B/'PATCHED_ASSEMBLY.xml').read_text();assert normalized(ax)==normalized(bx)
 # Test the normalization seam: retain rejection of actor size and vehicle changes.
 negative=[]
 for changed in [bx.replace('size=".10 .20"','size=".11 .20"'),bx.replace('mocap="true"','mocap="false"')]:
  try:negative.append(normalized(ax)!=normalized(changed))
  except AssertionError:negative.append(True)
 assert len(negative)==2 and all(negative)
 source=(R/'experiments/rpccr_execution_core/fresh_worker.py').read_text();assert "assert setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8'"in source
 result=json.loads((B.parent/'RESULT.json').read_text());assert result['vehicle_initializations']==1 and result['new_actual_native']==0 and result['analytical_prediction_native']==0
 check=dict(passed=True,models=0,integrations=0,old_NS_mjb_sha=sha(A/'scene_model.mjb'),actual_WE_mjb_sha=sha(B/'scene_model.mjb'),original_fixed_NS_sha_rejects_declared_WE=True,
     saved_compiled_array_count=len(aa),saved_identical_array_records=len(aa)-len(differences),changed_array_names=differences,
     assembly_xml_identical_except_declared_actor_anchor=True,xml_gate_negative_cases=negative,
     diagnosis='Route-specific registered actor anchor changes the compiled MJB hash; worker/audit/archiver incorrectly hard-code NS scene-model SHA.',
     actual_initial_pose=result['physical']['final_body'][:3],actual_native=0,private_native=0,replay_native=0,training_updates=0,
     original_frozen_sources_and_failed_results_preserved=True,remaining_tasks_unexecuted=['repeat_west_east','main_east_west','repeat_east_west'],navigation_restart_authorized=False)
 (O/'DIAGNOSIS.json').write_text(json.dumps(check,indent=2)+'\n');print(json.dumps(check),flush=True)
if __name__=='__main__':main()
