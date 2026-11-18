"""Production recovery policy on analytical state proxies, never a vehicle."""
from route_tools import *
import importlib.abc,types,copy,ast,subprocess,signal,traceback,fcntl
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('NO_PHYSICAL_MODEL_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModels())
import route_policy as policy
def main():
    assert not read(O/'APPROVAL.json')['models_authorized']and sha(R/'REVIEW_PENDING')==GUARD
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V1184_QUALIFICATION_300S')));signal.alarm(300)
    begin=time.monotonic();cpp=py=0;results=[];negative=[]
    for t in read(C/'TASKS.json'):task_contract(t)
    for p in C.glob('*.py'):ast.parse(p.read_text())
    start=load('v1184_scope_check',C/'start.py');a=read(O/'AUTHORIZATION.json');assert start.validate_authorization(a)==5400
    for k,value in [('authorized',False),('window_seconds',7200),('window_seconds',5400.),('automatic_new24',True),('stop_on_first_failure',False)]:
        try:start.validate_authorization(dict(a,**{k:value}))
        except AssertionError:negative.append(k)
        else:raise AssertionError('AUTH_NEGATIVE_ACCEPTED '+k)
    w=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=time.time()+10,hard_stop_monotonic=time.monotonic()+10)
    assert remaining(w)>0 and remaining(dict(w,absolute_deadline_unix=0))<0 and remaining(dict(w,hard_stop_monotonic=0))<0
    for name in ['worker.py','audit.py','campaign.py','finish.py','watchdog.py']:load('v1184_import_'+name.replace('.','_'),C/name)
    worker=load('v1184_no_authority',C/'worker.py');saved=sys.argv[:];sys.argv=['worker',str(C/'TASK_main_NORTH_SOUTH.json')]
    try:
        try:worker.main()
        except AssertionError as e:assert 'NO_NEW_MODEL_AUTHORITY'in str(e);negative.append('worker_no_authority')
        else:raise AssertionError('WORKER_AUTHORITY_BYPASSED')
    finally:sys.argv=saved
    try:factory().create(O/'FORBIDDEN_MODEL',read(C/'TASK_main_NORTH_SOUTH.json'))
    except AssertionError as e:assert 'PHYSICAL_MODELS_DISABLED'in str(e);negative.append('factory_no_authority')
    else:raise AssertionError('FACTORY_AUTHORITY_BYPASSED')
    for case in ['NORTH_SOUTH','EAST_WEST']:
        x,rows=finite_plan(case);org=dict(q.initial(x['packet']),steering_load_episode=False);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);ss,uu,mm=engine.simulate(org,rows)
        class Proxy:
            def __init__(self):
                self.p=q.model.Predictor(x['setup'],org);self.adapter=self.p.adapter;self.adapter.commands.ids=np.arange(4);self.count=x['packet']['native_tick'];self.d=types.SimpleNamespace(ctrl=np.zeros(4));self.controls=[]
            def step(self,v,w,stale):
                _,u=self.p.step(v,w,stale);self.d.ctrl=u;self.controls.append(u);self.count+=1
            def scan(self):return None
        def measured(v):
            s=v.p.state;p=copy.deepcopy(x['packet']);p['body']=[*s[:3],s[3],s[5]];p['body_lateral']=s[4];p['native_tick']=v.count;p['sim_time']=v.count*.01;p['controller_memory']=dict(last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral));p['steering']['velocity']=[float(s[7]),float(s[7])];return p
        saved_packet=policy.packet;saved_state=policy.state;policy.packet=measured;policy.state=lambda v:v.p.state.copy();v=Proxy()
        try:answer=policy.run(v,x['setup'],x,rows,ss,lambda:time.monotonic()<begin+270,lambda _:None)
        finally:policy.packet=saved_packet;policy.state=saved_state
        py+=2*v._route_python_native;tablepath=R/('runs/v1181_remaining_route_transfer/'+case+'_TABLE.npz')
        with np.load(tablepath)as z:table={k:z[k].copy()for k in z.files}
        g=q.Geometry(x,table);shadow=v._route_shadow;raw=float(np.minimum(*g.components(shadow[:,:3],np.arange(len(shadow)))).min());assert raw>=q.REQUIRED and g.cycle(shadow[-1:,:3])[0]>=q.REQUIRED
        replay=[q.accelerator.row(*row['request'][:2],mode=row['parked_target']is not None,target=row['parked_target']or 0.)for row in v._route_journal]
        cs,cu,cm=engine.simulate(org,replay);error=max(float(abs(cs-shadow).max()),float(abs(cu-np.array(v.controls)).max()));assert error<=1e-8
        cpp+=engine.native;results.append(dict(case_id=case,production_policy_passed=True,reference_native=len(ss)-1,feedback_native=v._route_python_native,raw=raw,maximum_cpp_python_error=error,goal_distance_m=answer['goal_distance_m'],synthetic_analytical_state_proxy_only=True))
    # WE's exact policy and full saved-data audit were already qualified in V1180.
    parent=read(R/'runs/v1180_fresh_recovery_chain/FINALIZED.json');assert parent['fresh_known_course_main_repeat_passed']and parent['manifest_readback']
    original=load('v1184_normal_owner_rehearsal',R/'experiments/v1180_fresh_recovery_chain/chain_tools.py');owner=configure_owner(O,time.time()+500);assert callable(owner.navigate)and callable(owner.execute)
    from brake_reserve import Reserve
    import kernel
    kernel.remaining_root=lambda:300.
    reserve_checks=[]
    for case in ['NORTH_SOUTH','EAST_WEST','WEST_EAST']:
        m=read(R/('runs/v1122_cache_entry_relay/'+case+'_T0_METADATA.json'))
        reserve=Reserve(m['setup']);proof=reserve.check(m['packet'],np.zeros((5,3)))
        assert proof['current_stop_passed'] and proof['passed']
        reserve_checks.append(dict(case_id=case,proof=proof))
    dump(O/'ANALYTICAL_ENTRY_QUALIFICATION.json',dict(passed=True,checks=reserve_checks,analytical_preview_native_at_least=13215,models=0,new_mujoco_native=0))
    # Disallow external control histories before touching the file content.
    code="from route_tools import *\nold.history_guard(O/'not_an_actual_output')\ntry:\n open(R/'runs/v858_nav2_verified/v1180/main/physics/BODY_COMMANDS.json').read()\nexcept AssertionError as e:\n assert 'FRESH_HISTORY_READ_FORBIDDEN'in str(e)\nelse:raise AssertionError('OLD_HISTORY_ACCEPTED')\n"
    cp=subprocess.run([sys.executable,'-B','-c',code],cwd=C,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30);assert cp.returncode==0,cp.stdout;negative.append('external_history_read')
    for t in read(C/'TASKS.json'):
        for key,value in [('historical_prefix_native',1),('native_limit',85000),('scope','new24')]:
            try:task_contract(dict(t,**{key:value}))
            except AssertionError:pass
            else:raise AssertionError('TASK_NEGATIVE_ACCEPTED '+key)
    dump(O/'QUALIFICATION.json',dict(passed=True,cases=results,negatives=negative,original_WE_full_fixture_and_audit_reused_unchanged=True,models=0,new_mujoco_native=0,analytical_cpp_native=cpp,analytical_python_native=py,wall_s=time.monotonic()-begin,formal_retained_commit=False));print(json.dumps(results))
if __name__=='__main__':
    try:main()
    except BaseException as e:
        p=O/'PREPARATION_ERRORS.json';errors=read(p)if p.exists()else[];errors.append(dict(error=repr(e),traceback=traceback.format_exc(),physical_models=0,new_mujoco_native=0,analytical_partial_count_unknown=True));dump(p,errors);raise
