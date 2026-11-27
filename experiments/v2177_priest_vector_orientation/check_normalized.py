from pathlib import Path
import os,json,hashlib
import numpy as np
from collocation import Projection
from normalized import Normalized
R=Path(__file__).resolve().parents[2];S=R/'runs/v2177_priest_vector_orientation';assert os.sched_getaffinity(0)=={4}and not(S/'NORMALIZED_SOFTWARE_GATE.json').exists()
p=Projection(json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text()));n=Normalized(p);w=1e-4*np.sin(.31*np.arange(len(p.initial))+.29);r=n.evaluate(w);original=p.evaluate(n.original(w));roundtrip_error=float(abs(r['equalities']*n.eqscale-original['equalities']).max());assert np.array_equal(r['inequalities'],original['inequalities'])and roundtrip_error<=1e-14
lo,hi=n.bounds();oldlo,oldhi=p.bounds();assert np.allclose(n.original(lo),oldlo,equal_nan=True)and np.allclose(n.original(hi),oldhi,equal_nan=True)
err=0.;checks=0
for j in [0,2,10,30,60,75,91]:
 a=w.copy();b=w.copy();a[j]+=1e-7;b[j]-=1e-7;up=n.evaluate(a);dn=n.evaluate(b)
 err=max(err,float(abs((up['equalities']-dn['equalities'])/2e-7-r['equality_jacobian'][:,j]).max()),float(abs((up['inequalities']-dn['inequalities'])/2e-7-r['inequality_jacobian'][:,j]).max()));checks+=len(r['equalities'])+len(r['inequalities'])
assert err<1e-5
zero=n.evaluate(np.zeros_like(w));singular=np.linalg.svd(zero['equality_jacobian'],compute_uv=False);rank=int(np.count_nonzero(singular>singular.max()*1e-12));assert rank==p.N*3
result=dict(passed=True,scope='ALGEBRAIC_NORMALIZATION_AND_EQUALITY_RANK_ONLY',free_variables=len(w),equality_rows=p.N*3,equality_rank=rank,nonzero_singular_min=float(singular.min()),singular_max=float(singular.max()),equality_condition_number=float(singular.max()/singular.min()),FD_entries=checks,max_FD_error=err,row_scale_roundtrip_max_error=roundtrip_error,row_scale_roundtrip_byte_exact=(roundtrip_error==0.),inequality_zero_levels_unchanged=True,all_bounds_and_fixed_endpoints_unchanged=True,pure_SVD_calls=1,optimizer_NLP_model_physics_Source_calls=0,source_SHA256={str(z.relative_to(R)):hashlib.sha256(z.read_bytes()).hexdigest()for z in [Path(__file__),Path(__file__).parent/'normalized.py',Path(__file__).parent/'collocation.py']})
(S/'NORMALIZED_SOFTWARE_GATE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
