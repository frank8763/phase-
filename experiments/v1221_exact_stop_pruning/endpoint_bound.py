"""Exact sampled-point upper bounds for rejection only; never accepts."""
import copy,time

def upper_bound(q,original,stops,x,table,rows,states,memory,deadline,incumbent=None):
 np=q.np;engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);g=q.Geometry(x,table);flags=stops.flags_before(rows);offset=0;boundaries=[]
 while offset<len(states)-1:
  suffix=original.remaining_rows(rows,offset);first=suffix[0];n=int(first[2])if first[3]or first[1]==0. else min(8,int(first[2]));boundaries.append((offset,n));offset+=n
 indices=np.array([k for k,n in boundaries]);a,b=g.components(states[indices,:3],indices);order=sorted(zip(np.minimum(a,b),boundaries),key=lambda a:(a[0],a[1][0]));best=None
 for _,(offset,n)in order:
  assert time.monotonic()<deadline,'EXACT_POINT_BOUND_DEADLINE'
  block=original.front(original.remaining_rows(rows,offset),n);origin=dict(state=states[offset],last_ctrl=memory[offset,:4],integral=float(memory[offset,4]),**flags[offset]);p=stops.forecast(x,states[offset],memory[offset],offset);local=copy.copy(g);local.original=copy.copy(g.original);local.original.start=p['sim_time']
  for kind,schedule in [('current',[(0.,0.,2200,0)]),('prospective',[*block,(0.,0.,2200,0)])]:
   ss,_,_=engine.simulate(origin,schedule);length=len(ss)-1;head=0 if kind=='current'else n
   probe=sorted({0,length,head,*[min(length,head+k)for k in [8,16,32,64,96,128,192,256,384,512,768,1024,1536,2200]]})
   a,b=local.components(ss[probe,:3],np.asarray(probe));raws=np.minimum(a,b);j=int(np.argmin(raws));raw=float(raws[j]);cycle=float(local.cycle(ss[-1:,:3])[0]);w=dict(offset=offset,prefix=n,kind=kind,relative_native=int(probe[j]),raw_m=raw,upper_bound_m=raw+1e-9)
   if best is None or raw<best['raw_m']:best=w
   if raw<q.REQUIRED-1e-9 or cycle<q.REQUIRED-1e-9:return dict(upper_bound_m=best['upper_bound_m'],witness=best,refusal_witness=dict(w,cycle_raw_m=cycle),analytical_cpp_native=engine.native)
   if incumbent is not None and raw+1e-9<incumbent:return dict(upper_bound_m=raw+1e-9,witness=w,refusal_witness=None,analytical_cpp_native=engine.native)
 return dict(upper_bound_m=best['upper_bound_m'],witness=best,refusal_witness=None,analytical_cpp_native=engine.native)
