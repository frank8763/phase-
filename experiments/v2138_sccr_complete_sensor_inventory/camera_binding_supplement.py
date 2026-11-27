"""Late static binding diagnostic, never loads a model or reruns old extraction."""
from pathlib import Path
import ast,hashlib,json,os,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert os.sched_getaffinity(0)=={4}
 result=json.loads((S/'RESULT.json').read_text());assert result['passed']and result['closed']
 assert all(sha(R/n)==h for n,h in result['input_SHA256'].items())
 o=R/'runs/v2137_psf_progress_control';assert json.loads((o/'DISPATCH_RESULT.json').read_text())['finite_queue_completed']
 barrier=o/'components/PSF/POST_COMPONENT_STORAGE_BARRIER.json';assert json.loads(barrier.read_text())['passed']
 p=R/'runtime/mk-mini/training/envs/mkmini_real_indoor_phase3_depth_astar_sac_env.py';t=ast.parse(p.read_text())
 names=[n.value.value for n in ast.walk(t)if isinstance(n,ast.Assign)and isinstance(n.value,ast.Constant)and isinstance(n.value.value,str)and any(isinstance(x,ast.Attribute)and x.attr=='depth_camera_name'for x in n.targets)]
 assert names==['d435i_depth']
 assembly=o/'components/PSF/actual/physics/PATCHED_ASSEMBLY.xml';root=ET.parse(assembly).getroot()
 assert not list(root.iter('include')),'STATIC_CAMERA_INVENTORY_MUST_RESOLVE_INCLUDES'
 cameras=[dict(x.attrib)for x in root.iter('camera')];available=[x.get('name')for x in cameras]
 assert 'd435i_depth_camera'in available
 requested=names[0];assert requested not in available
 # Pure name-binding regression: actual saved XML fails the declared lookup;
 # its existing name is a possible NEW adapter binding, not a source repair.
 original_lookup_matches=[x for x in cameras if x.get('name')==requested]
 proposed_lookup_matches=[x for x in cameras if x.get('name')=='d435i_depth_camera']
 assert len(original_lookup_matches)==0 and len(proposed_lookup_matches)==1
 z=dict(passed=True,closed=True,scope='LATE_STATIC_CAMERA_BINDING_DIAGNOSIS_ONLY',original_requested_camera=requested,saved_current_assembly_cameras=cameras,original_name_present_in_saved_assembly=False,new_explicit_binding_candidate='d435i_depth_camera',new_candidate_is_not_admitted=True,no_model_or_camera_renamed=True,source_defines_missing_id_all_ones_fallback=True,actual_SCCR_full186_or_camera_availability_NOT_measured=True,does_not_prove_all_historical_runs_used_fallback=True,new_equal_sensor_confirmation_must_disclose_camera_binding_and_policy_input_distribution=True,previous_50_feature_software_proof_remains_partial=True,models=0,renderers=0,policy_inferences=0,physics=0,replay=0,formal_tasks=0,input_SHA256={str(x.relative_to(R)):sha(x)for x in [p,assembly,barrier,S/'RESULT.json']},helper_SHA256=sha(Path(__file__)),late_after_original_inventory_result=True)
 out=S/'CAMERA_BINDING_SUPPLEMENT.json';assert not out.exists();out.write_text(json.dumps(z,indent=2)+'\n')
 assert all(sha(R/n)==h for n,h in result['input_SHA256'].items());print(json.dumps(z))
if __name__=='__main__':main()
