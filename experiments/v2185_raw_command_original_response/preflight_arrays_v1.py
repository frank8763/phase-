"""Real in-memory NumPy NPZ bytes/readback only; no analytic backend imports."""
import ast,hashlib,io,json,os,subprocess,sys,zipfile
from pathlib import Path
from context import R,C,S,read,sha

def main():
    assert os.sched_getaffinity(0)=={0}and not(S/'ARRAY_FORMAT_PREFLIGHT.json').exists()
    assert not any((S/n).exists()for n in ['SOURCE_ONCE.json','NUMERICAL_ADMISSION.json','RUNTIME_ONCE.json'])
    import numpy as np
    total=0;rows=[]
    shapes={'states':(2206,8),'controls':(2205,4),'memory':(2206,5),'requests':(2205,3)}
    for method in ['DWA','RPP']:
        arrays={k:np.zeros(shape,dtype='<f8')for k,shape in shapes.items()};b=io.BytesIO();np.savez(b,**arrays);raw=b.getvalue()
        with zipfile.ZipFile(io.BytesIO(raw))as z:assert len(z.infolist())==4 and all(i.compress_type==zipfile.ZIP_STORED for i in z.infolist())
        with np.load(io.BytesIO(raw),allow_pickle=False)as z:assert set(z.files)==set(arrays)and all(np.array_equal(z[k],a)for k,a in arrays.items())
        count=sum(a.nbytes for a in arrays.values());total+=len(raw);rows.append(dict(method=method,raw_array_bytes=count,stored_npz_bytes=len(raw),overhead_bytes=len(raw)-count))
    assert sum(r['raw_array_bytes']for r in rows)==705808 and total<=705808+8192<2*1024**2
    # Real entry refuses inside this actual Phase namespace before imports.
    p=subprocess.run([sys.executable,'-B',str(C/'entry.py')],cwd=R,capture_output=True,timeout=10)
    assert p.returncode==77 and json.loads(p.stdout)['refused_before_numerical_import']and not p.stderr
    assert not any(n in sys.modules for n in ['backend','numeric','kernel','model','mujoco','torch','vehicle','factory'])
    for path in C.glob('*.py'):ast.parse(path.read_text())
    v=dict(passed=True,scope='CONSTANT_ARRAY_REAL_NUMPY_ZIP_STORED_SIZE_READBACK_NOT_MODEL_OR_PHYSICAL_IO',numpy_version=np.__version__,cases=rows,total_stored_bytes=total,unchanged_predictive_payload_cap=2*1024**2,no_compression_credit=True,no_payload_files_written=True,real_isolated_unadmitted_CLI_returncode=77,analytic_backend_imports_constructors_steps_actual_physics_replay_Source=0,new_original_physical_recorder_or_future_contact_capacity_qualified=False,input_precharge_sha256=sha(S/'STORAGE_PRECHARGE.json'),checker_sha256=sha(Path(__file__)))
    raw=json.dumps(v,sort_keys=True,separators=(',',':')).encode()+b'\n';assert len(raw)<=4096
    with(S/'ARRAY_FORMAT_PREFLIGHT.json').open('xb')as f:f.write(raw)
    print(json.dumps({'passed':True,'total_stored_bytes':total,'original_arrays_raw_bytes':705808,'isolated_entry_refusal':77,'actual_models':0}))
if __name__=='__main__':main()
