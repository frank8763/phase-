from pathlib import Path
import ast,concurrent.futures,hashlib,json,os,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
GAPS={'SCCR':['original186obs requires50camera/depth features plus riskfusion depth; current32ray contract incompatible'],'MPPI':['coherent/deadband adapter current causal map/time/vehicle binding','fixed sample/RNG bookkeeping and original tail/response','complete capture/replay/audit qualification'],'SVG-MPPI':['author velocity/steering/current scan interface','vehicle gear/curvature mapping without clipping','full original response and retained stop production binding'],'PRIEST':['declared author variant and optimizer input identity','car gear/curvature mapping and controller wiring','complete current causal response/evidence binding'],'PSF':['full faithful vehicle implementation missing','nominal controller/model/constraint/terminal contract and solver missing'],'PCBF':['full faithful recovery/barrier vehicle implementation missing','same PSF nominal/model/constraints contract and solver missing']}
def work(item):
 method,cpu=item;os.sched_setaffinity(0,{cpu});start=time.monotonic();old=read(R/'runs/v1936_seven_method_launch_bundle/methods'/method/'AVAILABLE_ASSET_PINS.json');assets=[]
 for row in old['files']:
  p=R/row['path'];entry=dict(path=row['path'],exists=p.is_file(),source_imported=False)
  if p.is_file():
   entry.update(bytes=p.stat().st_size,sha256=sha(p));assert entry['sha256']==row['sha256']
   if p.suffix=='.py':
    tree=ast.parse(p.read_text());entry['functions']=[dict(name=n.name,arguments=[a.arg for a in n.args.args])for n in tree.body if isinstance(n,ast.FunctionDef)];entry['imports']=[ast.unparse(n)for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
  assets.append(entry)
 slots=[v for v in read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')['slots']if v['method']==method];assert len(slots)==12 and all(not v['registered']for v in slots)
 result=dict(method=method,cpu=cpu,assets=assets,original12locked_tasks_sha256=sha(R/'runs/v1936_seven_method_launch_bundle/methods'/method/'LOCKED_ASSIGNMENTS.json'),formal_tasks_unclaimed=12,formal_ready=False,production_binding_exists=(R/'runs/v1936_seven_method_launch_bundle/methods'/method/'PRODUCTION_BINDING.json').exists(),remaining_concrete_work=GAPS[method],required_input_fields=['native_tick','sim_time','current body/steering/memory receipt','publicmap','current32ray','sourcebound path/goal'],forbidden_inputs=['actortruth','phase','seed','futureevaluatorstate','oldcontrolcertificate'],required_output_fields=['source_request_sha256','origin_native_tick','unmodifiedrawcommand','methodworkcounts_or_unknown'],original_contract=dict(position_error_m=.04,yaw_error_rad=.035,steering_error=.015,minimum_actual_m=.15,complete_tail=2200,errorstop_minimum=200,fullstate_replay_tolerance=1e-8),models=0,DLL_loads=0,optimizer_calls=0,physical_native=0,replay_native=0,wall_s=time.monotonic()-start)
 folder=O/method;folder.mkdir();put(folder/'INTERFACE_DOSSIER.json',result);return dict(method=method,cpu=cpu,formal_ready=False,assets=len(assets),wall_s=result['wall_s'])
def main():
 start=time.monotonic();assert not(O/'ONCE_CLAIM.json').exists();ledger=R/'runs/v1805_common_algorithm_registry/LEDGER.json';before=sha(ledger);put(O/'ONCE_CLAIM.json',dict(pid=os.getpid(),unix=time.time(),maximum_s=120,models=0));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 items=[(m,[4,6,8][i%3])for i,m in enumerate(GAPS)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(work,items))
 assert sha(ledger)==before and time.monotonic()-start<120;put(O/'RESULT.json',dict(passed=True,closed=True,preparation_only=True,three_worker_cpu_ids=[4,6,8],methods=results,all_remaining72tasks_unclaimed=True,ledger_sha256_unchanged=before,models=0,solver_calls=0,actual_native=0,replay_native=0,formal_ready_methods=0,wall_s=time.monotonic()-start));print(json.dumps(read(O/'RESULT.json')))
if __name__=='__main__':main()
