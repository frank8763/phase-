"""EXPLICIT FAKE admission/SciPy in readonly Phase; never a production worker."""
from pathlib import Path
import sys,json,types,hashlib
import numpy as np
import peer_entry as m
S=Path(__file__).resolve().parents[2]/'runs/v2180_fresh_projection_component/software_socket'
a_path=S/'ADMISSION_FIXTURE.json';a=json.loads(a_path.read_bytes());claim=json.loads((S/'CLAIM_FIXTURE.json').read_bytes());calls=[0]
def fake(fun,x0,*,jac,bounds,constraints,method,options):
 calls[0]+=1;assert calls[0]==1 and method=='SLSQP'
 return types.SimpleNamespace(x=x0.copy(),fun=np.float64(fun(x0)),success=np.bool_(True),status=np.int64(0),message='EXPLICIT FAKE BACKEND; NO REAL NLP',nit=np.int64(1),nfev=np.int64(1),njev=np.int64(1))
scipy=types.ModuleType('scipy');scipy.__version__='1.14.1';opt=types.ModuleType('scipy.optimize');opt.minimize=fake;scipy.optimize=opt;sys.modules['scipy']=scipy;sys.modules['scipy.optimize']=opt
m.authority=lambda:(a,{},{});prior=m.sha;m.sha=lambda p:hashlib.sha256(a_path.read_bytes()).hexdigest()if Path(p).name=='PROJECTION_OPTIMIZER_ADMISSION.json'else prior(p);m.read=lambda p:claim if Path(p).name=='PROJECTION_PEER_ONCE.json'else (_ for _ in()).throw(AssertionError('UNEXPECTED_REAL_AUTHORITY_READ'))
raise SystemExit(m.main())
