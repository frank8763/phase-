"""Prepare one time-labelled reference revision; no simulator or model access."""
import pathlib,json,shutil
repo=pathlib.Path(__file__).resolve().parents[2];old=repo/'experiments/v807_reactive_single_task_continuation';own=repo/'experiments/v808_timed_reference_qualification'
assert not(own/'CANDIDATE_FREEZE.json').exists()
assert not own.exists()or{p.name for p in own.iterdir()}=={'timed_reference.py'}
own.mkdir(exist_ok=True)
for n in ['planner.py','exact_footprint.py','motion_tracker.py','future_guide.py']:
 shutil.copy2(old/n,own/n)
# These pure dependencies are needed by the unchanged causal tracker import tree.
for p in old.glob('*.py'):
 if p.name not in ['run_static.py','execute_development.py','finalize_development.py']and not(own/p.name).exists():shutil.copy2(p,own/p.name)
s=(own/'planner.py').read_text();s=s.replace('def search(field,','def spatial_search(field,',1)
# Keep the original spatial implementation exact and a second time-labelled implementation.
fn=s[s.index('def spatial_search('):].replace('def spatial_search(','def timed_search(',1)
fn=fn.replace('def key(p,gear):return (','def key(p,gear,arrival):return (',1).replace(',gear)\n    poses=[start]',',gear,min(17,int(round(arrival/.4))))\n    poses=[start]',1)
fn=fn.replace('costs=[0.];best={key(start,1):0.}', 'costs=[0.];arrivals=[0.];best={key(start,1,0.):0.}')
fn=fn.replace('key(pose,gears[i])','key(pose,gears[i],arrivals[i])')
fn=fn.replace('vals=field.pose_values(dense.reshape(-1,3)).reshape(len(choices),30)', '''from timed_reference import REFERENCE_SPEED,SHIFT_TIME
        offsets=(np.arange(6)[:,None]+fractions[None,:])*(.04/REFERENCE_SPEED)
        starts=np.array([arrivals[i]+(SHIFT_TIME if gear!=gears[i]else 0.)for gear,st in choices])
        dense_times=starts[:,None,None]+offsets[None,:,:]
        vals=field.reference_values(dense.reshape(-1,3),dense_times.reshape(-1)).reshape(len(choices),30)
        if any(gear!=gears[i]for gear,st in choices):
            wt=arrivals[i]+np.linspace(0.,SHIFT_TIME,21)
            minimum_wait=float(field.reference_values(np.repeat([pose],21,axis=0),wt).min())
            for j,(gear,st)in enumerate(choices):
                if gear!=gears[i]:vals[j]=np.minimum(vals[j],minimum_wait)''')
fn=fn.replace('k=key(endpoint,gear)','arrival=arrivals[i]+.24/REFERENCE_SPEED+(SHIFT_TIME if gear!=gears[i]else 0.);k=key(endpoint,gear,arrival)')
fn=fn.replace('gears.append(gear);costs.append(new)','gears.append(gear);costs.append(new);arrivals.append(arrival)')
start=fn.index('    chain=[];i=selected');end=fn.index('    return path,',start)
fn=fn[:start]+'''    chain=[];times_chain=[];i=selected
    while parents[i]>=0:
        parent=parents[i];wait=SHIFT_TIME if gears[i]!=gears[parent]else 0.
        chain.append(np.column_stack((pieces[i],np.full(6,gears[i]))))
        times_chain.append(arrivals[parent]+wait+np.arange(1,7)*(.04/REFERENCE_SPEED));i=parent
    path=np.vstack((np.r_[start,1.],*reversed(chain)));schedule=np.r_[0.,np.concatenate(list(reversed(times_chain)))]
    from timed_reference import scheduled_samples
    dense,dtimes=scheduled_samples(path,schedule)
    minimum=float(np.min(field.reference_values(dense,dtimes)))
    certificate_floor=required if dense_requested_guard else hard
    if minimum<certificate_floor-1e-8:return None,{'status':'DENSE_TIME_REFERENCE_REJECTED','clearance_m':minimum,'required_m':certificate_floor,'expanded':expanded}
''' +fn[end:]
fn=fn.replace("'guard_m':required}","'guard_m':required,'reference_arrival_times_s':schedule.tolist(),'temporal_reference_horizon_s':6.56,'uncertified_beyond_horizon_reference_nodes':int(np.sum(schedule>6.56)),'reference_speed_m_s':REFERENCE_SPEED,'reference_not_execution_certificate':True}")
s+='\n\n'+fn+'''\n\ndef search(field,*args,**kwargs):
    if getattr(field,'temporal_state',None)is None:return spatial_search(field,*args,**kwargs)
    return timed_search(field,*args,**kwargs)
'''
(own/'planner.py').write_text(s)
print(json.dumps({'prepared':str(own),'models':0,'integrations':0}))
