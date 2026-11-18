from bridge_tools import *
import fcntl,hashlib
def read(p):return json.loads(p.read_text())
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=read(O/'COMPLETION.json');assert d['error']is None and d['main_records']==17600 and not d['parallel_unreturned_work_unknown']
    f=read(C/'SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in f.items())
    regression=read(O/'MEASURED_REGRESSION.json');records=0;maximum=0.
    for row in regression['cases']:
        with np.load(O/(row['component']+'_residual.npz'))as z:b,a,pred,res,cp,eta,mem,req,native=[z[k].copy()for k in ['before','actual','predicted','residual','primitive_predicted','primitive_innovation','memory','request','native_before']]
        delta=pred-a;delta[:,2]=np.angle(np.exp(1j*delta[:,2]));assert abs(delta-res).max()<=1e-14 and np.array_equal(native,np.arange(len(a)))
        # Independent complex-plane inverse of the stored primitive coordinates.
        coord=cp+eta;turn=coord[:,2]+.005*(b[:,5]+coord[:,5]);body=.005*((b[:,3]+coord[:,3])+1j*(b[:,4]+coord[:,4]))+coord[:,0]+1j*coord[:,1];xy=body*np.exp(1j*(b[:,2]+turn/2))
        restored=np.column_stack([b[:,0]+xy.real,b[:,1]+xy.imag,b[:,2]+turn,coord[:,3:6],b[:,6]+.01*coord[:,7]+coord[:,6],coord[:,7]])
        e=primitive.maximum_error(restored,a);maximum=max(maximum,e);assert e<=1e-8
        assert np.array_equal(abs(res).max(0),row['observed_residual_abs_max'])and len(a)==row['actual_records'];records+=len(a)
        owner=q.model.Predictor(read(R/'runs/v1173_rate_preconditioned_input/INPUTS.json')['setup'],origin(b[0],mem[0],False)).adapter
        for i,(v,w)in enumerate(req):
            assert abs(owner.last-mem[i,:4]).max()<=1e-8 and abs(owner.integral-mem[i,4])<=1e-8
            owner.compute(v,w,b[i,3],b[i,5],False)
    assert records==17600
    stop=read(O/'REFERENCE_STOP_AUDIT.json');jobs=read(C/'TASKS.json')['reference_stop_jobs'];rows=stop['rows'];assert len(jobs)==len(rows)==d['cpp_stop_jobs']
    for j,r in zip(jobs,rows,strict=True):assert j['id']==r['id']and j['offset']==r['offset']and r['passed']==all(r['checks'].values())and r['completed_analytical_native']==2200
    failed=[r for r in rows if not r['passed']];assert len(failed)==stop['rejected']and stop['first_refused']==(failed[0]if failed else None)and stop['worst']==min(rows,key=lambda r:r['minimum_raw'])
    chosen=sorted(set([stop['worst']['id'],failed[0]['id']if failed else 0]));selected=read(R/'runs/v1160_safe_terminal_connection/SELECTED.json');x=selected['input'];params=q.model.parameters()
    with np.load(R/selected['table_path'])as z:table={k:z[k].copy()for k in ['bounds','centers']}
    geometry=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],params['coefficients']);witness=[]
    # Independent timed support expression, retaining original causal upper table.
    sys.path.insert(0,str(R/'experiments/v1135_causal_batch'));from geometry import NORMALS
    for ident in chosen:
        job=jobs[ident];old=rows[ident];ss,uu,mm=engine.simulate(job['origin'],[(0.,0.,2200,0)]);tick=np.arange(2201)+job['offset'];yaw=ss[:,2,None]
        footprint=.44*abs(np.cos(yaw)*NORMALS[:,0]+np.sin(yaw)*NORMALS[:,1])+.375*abs(-np.sin(yaw)*NORMALS[:,0]+np.cos(yaw)*NORMALS[:,1]);dynamic=(ss[:,:2]@NORMALS.T-footprint-geometry.upper(tick)-.1).max(1);static=geometry.static.clearances(ss[:,:3])[0];raw=np.minimum(static,dynamic)
        assert abs(float(raw.min())-old['minimum_raw'])<=1e-10
        for a,key in [(ss,'state_sha256'),(uu,'ctrl_sha256'),(mm,'memory_sha256')]:assert hashlib.sha256(np.ascontiguousarray(a,dtype=np.float64).tobytes()).hexdigest()==old[key]
        name=f'witness_stop{ident:04d}';np.savez_compressed(O/(name+'.npz'),states=ss,controls=uu,memory=mm,static=static,dynamic=dynamic,raw=raw,relative_ticks=tick);witness.append(dict(job=ident,saved_full_stop=name+'.npz',minimum_raw=float(raw.min())))
    assert d['analytical_python_native']==17600 and d['analytical_cpp_native']==17600+2200*len(rows)
    result=dict(passed=True,main_records=records,repeat_records_not_merged=17600,maximum_primitive_inverse_error=maximum,source_files=len(f),source_unchanged=True,reference_stop_jobs=len(rows),nominal_stops_passed=stop['passed'],nominal_stops_refused=stop['rejected'],witnesses=witness,analytical_cpp_native=engine.native,new_python_state_prediction=0,models=0,physical_native=0,universal_error_support_verified=False)
    dump(O/'FINAL_INDEPENDENT_AUDIT.json',result);print(json.dumps(result));fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
