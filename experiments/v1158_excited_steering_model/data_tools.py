"""Pinned measured inputs; no physical factories or state propagation."""
from pathlib import Path
import importlib.util
import sys
import numpy as np

C=Path(__file__).resolve().parent;R=C.parents[1]
spec=importlib.util.spec_from_file_location('v1158_old_measured_data',R/'experiments/v1154_measured_model_error/audit.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)


def add_load_flags(d):
    # Registered entry: predictor installed with episode OFF at canonical
    # stopped source. Subsequent mode is reconstructed from recorded inputs.
    loaded=False;flags=[]
    for command,parked in zip(d['commands'],d['modes']):
        flags.append(loaded)
        if parked or command[1]<=-.005:loaded=False
        elif command[1]>=.005:loaded=True
    d['load_flags']=np.array(flags,bool)
    return d


def old_data():return [add_load_flags(old.dataset(*info))for info in old.CASE_SPECS]


def response_data():
    rel='runs/v858_nav2_verified/v1157/response_main';p=R/rel
    setup=old.read(p/'physics/SETUP.json');packet=old.read(p/'ACTUAL_INITIAL_PACKET.json')
    journal=old.read(p/'REQUEST_JOURNAL.json');commands=np.asarray(old.read(p/'physics/BODY_COMMANDS.json'),float)
    with np.load(p/'physics/NATIVE_TRACE.npz')as z:
        q=z['qpos'].copy();v=z['qvel'].copy();ctrl=z['ctrl'][:,setup['actuator_ids']].copy();clock=z['time'].copy()
    after,front,rates=old.project(q,v,setup);n=len(q)
    assert n==8862 and len(journal)==len(commands)==n
    states=np.vstack([old.initial(packet)['state'],after])
    fronts=np.vstack([packet['steering']['position'],front]);frates=np.vstack([packet['steering']['velocity'],rates])
    memory=np.array([[*j['last_ctrl'],j['integral']]for j in journal])
    assert np.max(abs(clock-(np.arange(n)+1)*.01))<=1e-8
    for i,j in enumerate(journal):
        assert j['before_native']==i and j['applied'] and np.array_equal(np.array(j['request'],float),commands[i,[1,2,5]])
        prior=np.asarray(packet['controller_memory']['last_ctrl'])if not i else ctrl[i-1]
        old.aligned(commands[i],states[i],memory[i,:4],prior)
        if i:assert abs(memory[i,4]-old.expected_memory(memory[i-1,4],commands[i-1],states[i-1],False))<=1e-8
    result=old.read(p/'RESULT.json');audit=old.read(p/'FINAL_INDEPENDENT_AUDIT.json')
    assert result['passed']and audit['passed']and not audit['synthetic_qualification']
    d=dict(label='new_response',path=rel,begin=0,end=n,setup=setup,packet=packet,states=states,
        front=fronts,front_rate=frates,commands=commands,controls=ctrl,memory=memory,
        flags=np.zeros((n,2),bool),modes=np.zeros(n,bool),targets=np.zeros(n),phases=[j['phase']for j in journal])
    return add_load_flags(d)


def origin(d,i):return dict(old.origin(d,i),steering_load_episode=bool(d['load_flags'][i]))


def inputs():
    paths=old.input_paths()
    for role in ['response_main','response_repeat']:
        p=R/'runs/v858_nav2_verified/v1157'/role
        paths.extend(p/f for f in ['RESULT.json','FINAL_INDEPENDENT_AUDIT.json','ACTUAL_INITIAL_PACKET.json',
             'REQUEST_JOURNAL.json','physics/SETUP.json','physics/BODY_COMMANDS.json','physics/NATIVE_TRACE.npz'])
    return paths
