"""Same actual V1144 refusal packet/controls; old versus causally refreshed set."""
import sys, json, gzip, time, types, importlib.util, signal, hashlib, copy
from pathlib import Path
R = Path(__file__).resolve().parents[2]
O = R/'runs/v1146_causal_certificate_refresh'
sys.path.insert(0, str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
RESOURCE = apply()
sys.path.insert(0, str(R/'experiments/v1129_recording_entry_preparation'))
from result_io import dump, encode
import numpy as np
from refresh import causal_packets, try_commit, digest
# Bind the qualified controller before loading legacy measurement helpers;
# those helpers also expose generic module names used by older predictors.
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
from bindings import Adapter
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'))
from geometry import Geometry, REQUIRED
sys.path.insert(0,str(R/'experiments/v1118_coupled_live_qualification'))
from runtime import Engine, initial, remaining_rows, python_replay


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    O.mkdir(parents=True, exist_ok=True)
    assert not (O/'QUALIFICATION.json').exists(), 'NO_OVERWRITE'
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('QUALIFICATION300')))
    signal.alarm(300)
    root = R/'runs/v858_nav2_verified/v1144/observation_main'
    saved = json.loads((root/'STOP_CERTIFICATES.json').read_text())[-1]
    packet = saved['packet']; assert packet['native_tick'] == 32515 and saved['offset'] == 12355
    setup = json.loads((root/'physics/SETUP.json').read_text())
    trace = np.load(root/'physics/NATIVE_TRACE.npz')
    q = trace['qpos'][32514]; v = trace['qvel'][32514]
    yaw = np.arctan2(2*(q[3]*q[6]+q[4]*q[5]), 1-2*(q[5]**2+q[6]**2))
    assert max(abs(np.r_[q[:2],yaw]-packet['body'][:3])) <= 1e-10
    assert max(abs(trace['ctrl'][32514,setup['actuator_ids']]-packet['controller_memory']['last_ctrl'])) <= 1e-10
    journal = json.loads((root/'MODE_JOURNAL.json').read_text())
    assert journal[12355]['native'] == 32515 and journal[12355]['integral'] == packet['controller_memory']['integral']
    scans = json.loads(gzip.open(root/'physics/SENSORS.json.gz','rt').read())
    # Explicit source selection is performed before estimator construction.
    # The rejected future suffix is retained and counted, never used to fit.
    prefix = [s for s in scans if s['native_tick'] <= packet['native_tick'] and s['time'] <= packet['sim_time']+1e-9]
    clean, duplicates = causal_packets(prefix, packet)
    causal = load('v1146_original_causal',R/'experiments/v1024_full_route_execution/causal.py')
    norm = load('v1146_original_norm',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
    estimator = causal.Evidence(setup['known']); estimator.periodic = norm.PeriodicSupport()
    for sample in clean: estimator.update(sample)
    source = estimator.source(types.SimpleNamespace(d=types.SimpleNamespace(time=packet['sim_time'])))
    dump(O/'CAUSAL_SOURCE.json', source); dump(O/'ACTUAL_REFUSAL_PACKET.json',packet)
    sys.path.insert(0,str(R/'experiments/v1135_causal_batch'))
    from joint_domain import Domain,NORMALS
    from geometry import Geometry, REQUIRED
    fresh = Domain(source['periodic']['vertices'])
    oldx = json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text())
    oldtab = np.load(R/'runs/v1135_causal_batch/domain/JOINT_TABLE.npz')
    old_domain = Domain(oldx['source']['periodic']['vertices'])
    # Intersection preserves every old halfspace even if hull roundoff changes.
    fresh.A = np.vstack([fresh.A,old_domain.A]); fresh.b = np.r_[fresh.b,old_domain.b]
    fresh.lower = np.maximum(fresh.lower,old_domain.lower); fresh.upper = np.minimum(fresh.upper,old_domain.upper)
    assert np.all(fresh.lower <= fresh.upper)
    assert fresh.optimize(np.zeros(6)).success, 'INTERSECTION_EMPTY'
    centers = oldtab['centers']; upper,dual,_ = fresh.table(centers)
    directions = np.array([[[nx,nx*np.sin(.32*t),nx*np.cos(.32*t),ny,ny*np.sin(.32*t),ny*np.cos(.32*t)] for nx,ny in NORMALS] for t in centers])
    residual = directions-np.einsum('tnj,jk->tnk',dual,fresh.A)
    independent_upper = np.einsum('tnj,j->tn',dual,fresh.b)+np.where(residual>=0,residual*fresh.upper,residual*fresh.lower).sum(axis=2)+1e-8
    assert np.all(dual>=0) and np.max(abs(independent_upper-upper)) <= 1e-9
    bounds = upper+.08*((2*np.pi/.32/256)/2+.075)+2e-7
    np.savez_compressed(O/'INTERSECTED_TABLE.npz',bounds=bounds,centers=centers,dual=dual,residual=residual,A=fresh.A,b=fresh.b,lower=fresh.lower,upper_box=fresh.upper)
    rows = json.loads((R/'runs/v1144_saved_entry_relay/software/ROWS.json').read_text())['rows']
    block=[]; left=8
    for target,speed,count,mode in remaining_rows(rows,12355):
        take=min(left,int(count));block.append((target,speed,take,mode));left-=take
        if not left: break
    schedules={'current':[(0.,0.,2200,0)],'prospective':[*block,(0.,0.,2200,0)]}
    engine = Engine(setup); oldg=Geometry(oldx,{k:oldtab[k] for k in ['bounds','centers']})
    x=dict(setup=setup,packet=packet,source=source,goal=[4.,-2.],safe_terminal_pose=[4.,-1.85,0.])
    newg=Geometry(x,dict(bounds=bounds,centers=centers)); oldproof={}; newproof={}; cross_error=0.
    for key,schedule in schedules.items():
        states,controls=engine.simulate(initial(packet),schedule)
        ps,pu,*_=python_replay(setup,initial(packet),schedule)
        cross_error=max(cross_error,float(abs(ps-states).max()),float(abs(pu-controls).max()))
        local=dict(x,goal=states[-1,:2].tolist(),safe_terminal_pose=states[-1,:3].tolist())
        oldproof[key],_=oldg.final(dict(local,source=oldx['source']),states,controls,schedule)
        newproof[key],_=newg.final(local,states,controls,schedule)
        assert oldproof[key]['states_sha256']==saved[key]['states_sha256'] and oldproof[key]['controls_sha256']==saved[key]['controls_sha256']
        assert abs(oldproof[key]['minimum_raw_m']-saved[key]['minimum_raw_m']) <= 1e-10
    assert oldproof['current']['passed'] and not oldproof['prospective']['passed'], 'OLD_RED_NOT_REPRODUCED'
    assert cross_error <= 1e-8
    candidate=dict(packet_sha256=digest(packet),nested_domain=True,duals_verified=True,source_native_tick=source['source_native_tick'],source_age_s=source['source_age_s'],table_sha256=hashlib.sha256((O/'INTERSECTED_TABLE.npz').read_bytes()).hexdigest())
    previous={'old_certificate':saved['current'],'packet_sha256':digest(packet)}
    bundle,commit=try_commit(previous,packet,lambda _:candidate,lambda p,c:newproof,time.monotonic,time.monotonic()+10)
    negatives=[]
    def reject(name,fn):
        try: fn()
        except (AssertionError,ValueError,KeyError,TypeError): negatives.append(name); return
        raise AssertionError('NEGATIVE_ACCEPTED '+name)
    reject('future_measurement',lambda:causal_packets(prefix+[scans[-1]],packet))
    bad=copy.deepcopy(clean[-1]);bad['ranges'][0]+=.01
    reject('contradictory_duplicate',lambda:causal_packets(clean+[bad],packet))
    reject('backwards_measurement',lambda:causal_packets(clean+[clean[-2]],packet))
    reject('stale_measurement',lambda:causal_packets(clean[:-2],packet))
    bad=copy.deepcopy(clean[-1]);bad['yaw']=float('nan')
    reject('nonfinite_measurement',lambda:causal_packets([bad],packet))
    for name,change in [('wrong_packet',dict(packet_sha256='wrong')),('nonnested_domain',dict(nested_domain=False)),('invalid_duals',dict(duals_verified=False)),('future_source',dict(source_native_tick=32516)),('stale_source',dict(source_age_s=.1))]:
        returned,outcome=try_commit(previous,packet,lambda p,c=change:dict(candidate,**c),lambda p,c:newproof,time.monotonic,time.monotonic()+10)
        assert returned is previous and not outcome['committed'];negatives.append(name)
    for name,proofs,clock,deadline in [('unsafe_next_block',oldproof,lambda:0.,1.),('timeout',newproof,lambda:2.,1.)]:
        returned,outcome=try_commit(previous,packet,lambda p:candidate,lambda p,c:proofs,clock,deadline)
        assert returned is previous and not outcome['committed'];negatives.append(name)
    result=dict(passed=bool(commit['committed']),scope='offline same actual failure state, not physical acceptance',old_red_reproduced=True,old=oldproof,refreshed=newproof,transaction=commit,negative_cases_rejected=negatives,causal_packet_count=len(clean),identical_duplicates_collapsed=duplicates,future_packets_excluded=len(scans)-len(prefix),latest_sensor_native=clean[-1]['native_tick'],decision_native=32515,source_age_s=source['source_age_s'],required_raw_m=REQUIRED,python_cpp_state_ctrl_error=cross_error,lp_calls=fresh.calls+old_domain.calls,models=0,physical_native=0,analytical_cpp_native=engine.native,analytical_python_native=sum(sum(r[2] for r in rows) for rows in schedules.values()),no_physical_restart=True,old_failure_unchanged=True,wall_s=time.monotonic()-started)
    dump(O/'QUALIFICATION.json',result);signal.alarm(0);print(encode(result))


if __name__=='__main__':main()
