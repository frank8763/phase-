"""Read-only cheap whole configuration checks BEFORE consuming onceSOURCE."""
import ast,os,time,json
from context import R,C,SOURCE as S,read,put,sha,predecessors_closed
from reserved_census import admission

def check():
 assert not(S/'SOURCE_ONCE.json').exists()
 assert predecessors_closed()
 auth=read(S/'AUTHORIZATION.json');assert auth['fixed_order']==['PCBF']and time.time()+auth['required_reserve_before_new_component_s']<auth['absolute_end_unix']
 task=read(S/'components/PCBF/PILOT_TASK.json');limits=read(S/'components/PCBF/LIMITS_DRAFT.json')
 assert task['maximum_control_native']==500 and task['maximum_current_native_queries']==100 and task['stop_native']==2200 and task['goal_xy']==[4.,-2.]and not task['formal_common_task']
 assert limits['python_native_cap']==25000000 and limits['cpp_native_cap']==150000000 and limits['maximum_actual_native']==limits['maximum_replay_native']==60000 and limits['maximum_task_evidence_bytes']==224*1024**2 and limits['remaining_archive_download_reserve_bytes']==272*1024**2
 assert all(not(S/'components/PCBF'/n).exists()for n in ['PILOT_ONCE_CLAIM.json','COMPLETION.json','OWNED_CHILD.json','actual'])
 for name in ['COMPONENT_INTERFACE_PROOF.json','PERSISTENT_PROTOCOL_PROOF.json','SOFT_PREDICTION_GATE_PROOF.json','MEASURED_CLOCK_REGRESSION.json','NATIVE_SERIALIZATION_PROOF.json','QUOTA_OUTPUT_BOUNDARY_PROOF.json','DISPATCHER_SOFTWARE_PROOF.json']:assert read(S/name)['passed'],name
 from software_checks import UNCHANGED
 for name in UNCHANGED:assert(C/name).read_bytes()==(R/'experiments/v2122_priest_quiescent_handoff'/name).read_bytes(),name
 assert(C/'filter.py').read_bytes()==(R/'experiments/v2134_pcbf_remaining_numeric/filter_minimal.py').read_bytes()
 assert(C/'scaled.py').read_bytes()==(R/'experiments/v2156_pcbf_pinned_scipy_entry/scaled.py').read_bytes()
 assert(C/'evidence_service.py').read_text()==(R/'experiments/v2151_psf_wrapper_identity_binding/evidence_service.py').read_text().replace('MAX_REBUILD_NATIVE=11100000','MAX_REBUILD_NATIVE=500000')
 for name in ['compact_json.py','metadata_pack.py']:assert(C/name).read_bytes()==(R/'experiments/v2151_psf_wrapper_identity_binding'/name).read_bytes()
 for p in C.glob('*.py'):ast.parse(p.read_text())
 import navigation,native_worker,native_client,peer_contract,filter_scope
 assert peer_contract.MAX_QUERIES==100
 source=(C/'navigation.py').read_text();assert 'range(100)'in source and 'cycle%10==0'in source and "assert shadow['passed']"in source and "assert admission['passed']"in source
 worker=(C/'native_worker.py').read_text();assert 'from serialization import dumps'in worker and 'modules.scaled.minimizer'in worker and 'coordinate_transforms=transforms'in worker
 from evidence import deliver
 for rid in [None,'PCBF']:compile(deliver(rid,preview=True),'v2162_transport_preflight','exec')
 reserve=admission()
 return dict(passed=True,models=0,new_NLP=0,physics=0,replay=0,source_once_not_consumed=True,one_component_100_queries=True,configuration_and_serialization_preflight=True,all_caps_original=True,reservation=reserve,source_files={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()})
if __name__=='__main__':
 value=check();put(S/'PRE_SOURCE_PREFLIGHT.json',value);print(json.dumps({k:v for k,v in value.items()if k!='source_files'}))
