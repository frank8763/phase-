"""One exact request-expression diagnosis; never instantiate the response Policy."""
import ast,fcntl,hashlib,importlib.abc,importlib.util,json,math,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 started=time.monotonic();assert sorted(os.sched_getaffinity(0))==[4]and os.environ.get('PHASE_REPO')==str(R)
 class NoNumeric(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','vehicle','factory'}:raise AssertionError('PURE_REQUEST_MATH_ONLY:'+name)
 sys.meta_path.insert(0,NoNumeric());load('original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 freeze=read(O/'SOURCE_FREEZE.json');assert all(sha(R/n)==h for n,h in freeze['files'].items())
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized'];assert time.time()<1795395600
  boundary=load('direction_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');budgets=load('direction_budget',R/'experiments/v1436_pathlib_control_rename/writer_budget.py');writer=budgets.WriterBudget(O,role='SUPERVISOR_LOG',maximum_bytes=2*1024**2,source_identity=sha(O/'SOURCE_FREEZE.json'))
  with boundary.OutputBoundary(O,writer.reserve):
   result=dict(passed=False,closed=False,scope='SOURCE_DERIVED_MATHEMATICAL_DIAGNOSIS',models=0,analytical_native=0,physical_native=0,Allocator_recomputations=0,replay_native=0,optimizer_calls=0,recorded_runtime_request=False)
   try:
    current=read(R/'runs/v1504_priest_namespace_worker/numeric/CURRENT_INPUT.json');proposal=read(R/'runs/v1504_priest_namespace_worker/SAVED_OPTIMIZER_PROPOSAL.json')['candidate'];origin=read(R/'runs/v1518_compact_parent_control/model/GENERATION_ORIGIN.json')
    assert current['input_sha256']=='7f320f7b39eb11a0a0aa90cfc8e956a8ad115ddb0275fc94328fa39eeefad8db'and proposal['proposal_sha256']=='c555bc9751cbad0cff168e0a6e925599898dba10027705d705c53adc18b2d8ea'
    assert origin['passed']and origin['modeled_numeric_packet']['body']==current['origin']['body']
    source=R/'experiments/v1485_priest_current_polynomial_seam/response_policy.py';tree=ast.parse(source.read_text());select=next(x for x in ast.walk(tree)if isinstance(x,ast.FunctionDef)and x.name=='select');cached=next(x for x in ast.walk(select)if isinstance(x,ast.If)and isinstance(x.test,ast.BoolOp)and ast.unparse(x.test).startswith('self.cached is None'))
    refusal=next(i for i,x in enumerate(cached.body)if isinstance(x,ast.Assert)and isinstance(x.msg,ast.Constant)and x.msg.value=='PRIEST_REQUEST_OPPOSES_DECLARED_SEGMENT_GEAR');pure=cached.body[:refusal];gate=cached.body[refusal].test
    allowed={'reply','elapsed','samples','vx','vy','speed','desired','error','vr','wr'};assert all(not isinstance(x,ast.Call)or not isinstance(x.func,ast.Attribute)or x.func.attr in {'sample','hypot','atan2','cos'}for node in pure for x in ast.walk(node))
    from types import SimpleNamespace
    env=dict(self=SimpleNamespace(proposal=proposal,origin=current['fixed_origin_native']),tick=current['fixed_origin_native'],b=current['origin']['body'],poly=load('original_pure_polynomial',R/'experiments/v1485_priest_current_polynomial_seam/polynomial.py'),math=math,wrap=lambda a:math.atan2(math.sin(a),math.cos(a)))
    exec(compile(ast.Module(body=pure,type_ignores=[]),str(source),'exec'),env)
    accepted=eval(compile(ast.Expression(body=gate),str(source),'eval'),env);assert not accepted,'SAVED_DIRECTION_REFUSAL_NOT_REPRODUCED'
    yaw=env['b'][2];projected=env['vx']*math.cos(yaw)+env['vy']*math.sin(yaw);assert abs(projected-env['vr'])<=1e-15
    result.update(passed=True,reproduced_original_sign_refusal=True,input_sha256=current['input_sha256'],proposal_sha256=proposal['proposal_sha256'],gear=proposal['reply']['gear'],body_yaw_rad=yaw,samples=env['samples'],mean_velocity_world=[env['vx'],env['vy']],mean_speed=env['speed'],desired_body_heading=env['desired'],heading_error_rad=env['error'],source_derived_raw_request=[env['vr'],env['wr']],body_forward_projection=projected,gear_gate_accepted=accepted,initial_sample_gear_gate_accepted=(abs(env['samples'][0]['velocity'][0]*math.cos(yaw)+env['samples'][0]['velocity'][1]*math.sin(yaw))<.005 or (env['samples'][0]['velocity'][0]*math.cos(yaw)+env['samples'][0]['velocity'][1]*math.sin(yaw))*proposal['reply']['gear']>0),extracted_request_source=ast.unparse(ast.Module(body=pure,type_ignores=[])),original_gate_source=ast.unparse(gate),source_hashes=freeze['files'],origin_yaw_exact=True,elapsed_s=env['elapsed'],sample_spacing_s=10/99,does_not_establish_independent_model_safety=True,no_new_method_or_revision=True)
   except BaseException as error:
    import traceback
    result.update(first_error=repr(error),traceback=traceback.format_exc())
   finally:
    result.update(closed=True,wall_s=time.monotonic()-started);raw=json.dumps(result,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<256*1024;temp=O/'RESULT.json.tmp';temp.write_bytes(raw);temp.replace(O/'RESULT.json')
  assert all(sha(R/n)==h for n,h in freeze['files'].items())and time.monotonic()-started<120
  print(json.dumps({k:result[k]for k in ['passed','reproduced_original_sign_refusal','source_derived_raw_request','mean_velocity_world','body_forward_projection','models','analytical_native']}))
if __name__=='__main__':main()
