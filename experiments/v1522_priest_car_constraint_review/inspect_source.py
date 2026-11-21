"""Read only exact author AST and saved outcomes; no imported author code."""
import ast,fcntl,hashlib,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));start=time.monotonic()
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0,source_only=True),f)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'and time.time()<1795395600
  prior=read(R/'runs/v1484_baseline_disposition_priest/AUTHOR_SOURCE_REVIEW.json');base=R/'runs/v1484_baseline_disposition_priest/upstream';members={v['path']:v for v in prior['source_members']};records={}
  for name,functions in {'priest/src/mpc_non_dy.py':['initial_alpha_d','compute_alph_d_proj','compute_cost_batch','compute_controls','compute_cem'],'priest/src/planner_nonhol_dy.py':[]}.items():
   path=base/name;assert sha(path)==members[name]['sha256'];text=path.read_text();tree=ast.parse(text);rows={}
   for node in ast.walk(tree):
    if isinstance(node,ast.FunctionDef)and node.name in functions:
     rows[node.name]=dict(first_line=node.lineno,last_line=node.end_lineno,arguments=[a.arg for a in node.args.args],self_attributes=sorted({x.attr for x in ast.walk(node)if isinstance(x,ast.Attribute)and isinstance(x.value,ast.Name)and x.value.id=='self'}),source=ast.get_source_segment(text,node),AST_sha256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest())
   records[name]=dict(sha256=sha(path),git_blob_sha1=members[name]['git_blob_sha1'],url=members[name]['url'],functions=rows,all_identifiers=sorted({x.id for x in ast.walk(tree)if isinstance(x,ast.Name)}),all_attributes=sorted({x.attr for x in ast.walk(tree)if isinstance(x,ast.Attribute)}))
  direction=read(R/'runs/v1520_priest_direction_diagnosis/RESULT.json');runtime=read(R/'runs/v1518_compact_parent_control/CLOSED_REVIEW.json');remote=read(R/'runs/v1518_compact_parent_control/actual_runtime_delivery/FULL_REMOTE_VERIFIED.json');assert direction['passed']and runtime['generation_analytic_native']==200 and runtime['nominal_native']==0 and remote['passed']
  cost=records['priest/src/mpc_non_dy.py']['functions']['compute_cost_batch'];projection=records['priest/src/mpc_non_dy.py']['functions']['compute_alph_d_proj'];assert not any(n in cost['self_attributes']for n in ['wheelbase','gear','steering','steering_rate'])and 'v_max'in projection['self_attributes']
  result=dict(closed=True,source_inspection_completed=True,runtime_qualification=False,models=0,analytical_native=0,physical_native=0,optimizer_calls=0,Allocator_recomputations=0,replay_native=0,new_revision=False,author_commit=prior['commit'],records=records,finite_disposition='ENGINEERING_ADAPTATION_REFUSED_ON_DISCLOSED_SAVED_COMPONENT;NOT_AUTHOR_ALGORITHM_FAILURE',whole_navigation=False,fair_paired_comparison=False,exact_car_demo_source_mapping='NOT_ESTABLISHED_FROM_SELECTED_PINNED_MEMBERS',no_claim_that_author_has_no_car_capability=True,blockers=['selected core projection has XY norm-speed/acceleration and obstacle residuals, not the original body/gear/actuator response contract','car-demo objective/source mapping and decentralized distribution recipe not established for selected dynamic ROS core','new signed-car proposal constraints would change method: preregister first, no silent objective change','full current response + independent audit and actual from-t0/before-detection lifecycle remain unqualified'],source_derived_direction_result_sha256=sha(R/'runs/v1520_priest_direction_diagnosis/RESULT.json'),closed_model_review_sha256=sha(R/'runs/v1518_compact_parent_control/CLOSED_REVIEW.json'),runtime_full_remote_proof_sha256=sha(R/'runs/v1518_compact_parent_control/actual_runtime_delivery/FULL_REMOTE_VERIFIED.json'),wall_s=time.monotonic()-start)
  raw=json.dumps(result,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<2*1024**2 and time.monotonic()-start<120;(O/'RESULT.json').write_bytes(raw)
  (O/'CLOSED_SOURCE_INDEX.json').write_text(json.dumps({str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()},indent=2)+'\n');print(json.dumps(dict(source_review_closed=True,models=0,new_revision=False,selected_author_car_demo_mapping_established=False)))
if __name__=='__main__':main()
