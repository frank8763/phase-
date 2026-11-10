"""Exercise the actual worker import, receiver and outgoing JSON; zero models."""
import copy,importlib.abc,importlib.util,json,subprocess,sys,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1020_terminal_two_route_development'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
def probe(version):
    sys.meta_path.insert(0,NoModel())
    import numpy as np
    p=R/'experiments'/version/'native_worker.py'
    spec=importlib.util.spec_from_file_location('actual_worker',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    cls=m.engine.Startup
    import inspect
    receiver=Path(inspect.getsourcefile(cls.receive)).resolve()
    # Only the adapter-switch hardware constructor is replaced. The production
    # receiver, command validation, packet projection and wire JSON all execute.
    owner=m.bound_native.original if hasattr(m,'bound_native') else sys.modules['native_contract']
    owner.switch=lambda vehicle,kind:dict(native_tick=vehicle.count,adapter='V958',physical_state_unchanged=True)
    def vehicle():
        return types.SimpleNamespace(count=100,m=types.SimpleNamespace(actuator_trnid=np.array([[0,0],[1,0]]),jnt_qposadr=np.array([0,1]),jnt_dofadr=np.array([0,1])),
            d=types.SimpleNamespace(time=1.,qpos=np.zeros(2),qvel=np.zeros(2)),adapter=types.SimpleNamespace(commands=types.SimpleNamespace(ids=[0,1]),last=np.zeros(4),integral=0.),body=lambda:[0.,0.,0.,0.,0.])
    def session():
        s=cls('wire-entry');s.phase='RUNNING';s.armed_at=0.;s.bind_vehicle(vehicle(),O);s.holding=True;s.active_profile_id=1
        s.vehicle.profile_status=dict(active=False,profile_id=1,completed_id=1,released_id=None);return s
    proof=dict(passed=True,v=0.,w=0.,issued_at=10.,source_native_tick=90,body_native_tick=100,body_age_s=.001)
    cmd=dict(kind='command',run_id='wire-entry',sequence=101,issued_at=10.,v=0.,w=0.,tube=proof)
    release=dict(kind='release_profile',run_id='wire-entry',issued_at=10.,profile_id=1,resume_command=cmd)
    s=session();s.receive(json.loads(json.dumps(release)),10.005,101,1.01)
    snap=dict(native_tick=100,time=1.,ranges=[3.],xy=[0.,0.],yaw=0.)
    packet=json.loads(json.dumps(m.engine.policy_packet('wire-entry',s.vehicle,snap,10.,10.006,'RUNNING')))
    green=receiver==(m.C/'native_contract.py').resolve() and s.command==cmd and packet['profile_status'].get('handoff_sequence')==101 and [x['decision']for x in s.receipts]==['PROFILE_RELEASED','ACCEPTED']
    negatives=[]
    if green:
        for name,change in [('missing',lambda x:x.pop('resume_command')),('moving',lambda x:x['resume_command'].update(v=.01)),('foreign',lambda x:x['resume_command'].update(run_id='foreign')),('late_body',lambda x:x['resume_command']['tube'].update(body_age_s=.051))]:
            bad=copy.deepcopy(release);change(bad);s0=session()
            try:s0.receive(bad,10.005,101,1.01)
            except BaseException:assert s0.holding and s0.command is None;negatives.append(name)
            else:raise AssertionError('INVALID_HANDOFF_ACCEPTED '+name)
        m.binding_receipt()
    return dict(passed=bool(green),receiver=str(receiver.relative_to(R)),wire_ack=packet['profile_status'].get('handoff_sequence'),decisions=[x['decision']for x in s.receipts],negative_cases=negatives,models=0,integrations=0)
def main():
    if len(sys.argv)>1:print(json.dumps(probe(sys.argv[1])));return
    results=[]
    for name,wanted in [('v1014_atomic_handoff_navigation',False),('v1020_terminal_two_route_development',True)]:
        p=subprocess.run([sys.executable,'-B',str(C/'qualify_backend.py'),name],capture_output=True,text=True,cwd=R,timeout=20)
        assert p.returncode==0,p.stderr
        row=json.loads(p.stdout);assert row['passed']is wanted,row;results.append(row)
    out=dict(passed=True,original_actual_entry_red=results[0],fixed_actual_entry_green=results[1],models=0,integrations=0)
    (O/'BACKEND_ENTRY_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
