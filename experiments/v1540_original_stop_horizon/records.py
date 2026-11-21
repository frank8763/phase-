"""Small complete/partial model evidence using already qualified bounded IO."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
codec=load('v1532_original_bounded_codec',R/'experiments/v1507_priest_response_evidence/branch_store.py')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save_json(folder,name,value,writer):
    assert Path(name).name==name
    path=folder/name;codec.write_atomic(path,codec.encoded(value),writer);return sha(path)
def binding(method):
    return dict(method_input_sha256=method['method_input_sha256'],physical_source_input_sha256=method['physical_source_input_sha256'],
                origin_native=method['fixed_origin_native'],origin_sim_time=method['fixed_origin_sim_time'],
                causal_snapshot_sha256=method['causal_snapshot_sha256'],geometry_kind='FULL_PERIOD_DISK',
                model_variant=method['model_variant'],method_epoch_revision=8,scientific_integration_revision=9)
def save_arrays(folder,name,arrays,writer):
    import numpy as np
    assert Path(name).name==name and name.endswith('.npz')
    buffer=io.BytesIO();np.savez_compressed(buffer,**arrays);data=buffer.getvalue();assert len(data)<=1024**2
    path=folder/name;codec.write_atomic(path,data,writer)
    with np.load(path,allow_pickle=False)as z:
        assert set(z.files)==set(arrays)
        for key,value in arrays.items():
            a=np.asarray(value);b=z[key]
            assert a.shape==b.shape and a.dtype==b.dtype and a.tobytes()==b.tobytes(),'STOP_ARRAY_BYTE_ROUNDTRIP'
    return dict(path=name,bytes=path.stat().st_size,sha256=sha(path),keys=sorted(arrays),bitwise_readback=True)
def read_complete(folder,receipt,method):
    import numpy as np
    assert receipt['binding']==binding(method) and receipt['complete']and receipt['native']==2200
    row=receipt['arrays'];path=folder/row['path'];assert path.parent==folder and path.stat().st_size==row['bytes']and sha(path)==row['sha256']
    with np.load(path,allow_pickle=False)as z:arrays={k:z[k].copy()for k in z.files}
    assert arrays['states'].shape==(2201,8)and arrays['ctrl'].shape==(2200,4)and arrays['memory'].shape==(2201,5)
    assert arrays['modes'].shape==(2201,3)and arrays['gear'].shape==(2201,3)
    assert arrays['native'].shape==arrays['sim_time'].shape==(2201,)
    assert all(np.isfinite(v).all()for v in arrays.values())
    assert np.array_equal(arrays['native'],method['fixed_origin_native']+np.arange(2201))
    assert np.max(abs(arrays['sim_time']-(method['fixed_origin_sim_time']+.01*np.arange(2201))))<=1e-8
    assert np.array_equal(arrays['requests'],np.zeros((2200,3)))
    return arrays
