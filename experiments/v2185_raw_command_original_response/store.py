"""Full arrays with original NumPy ZIP_STORED format, no compression credit."""
import io,json,zipfile
from context import S
META_CAP=128*1024;PAYLOAD_CAP=2*1024**2

def payload_used():return sum(p.stat().st_size for p in(S/'RUNTIME').rglob('*')if p.is_file())if(S/'RUNTIME').exists()else 0

def save_json(path,value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
    assert len(raw)<=32*1024 and path.resolve().is_relative_to((S/'RUNTIME').resolve())and payload_used()+len(raw)<=PAYLOAD_CAP
    with path.open('xb')as f:f.write(raw)

def stored_arrays(np,path,arrays):
    assert set(arrays)=={'states','controls','memory','requests'}
    assert all(a.dtype==np.float64 and a.ndim==2 and np.isfinite(a).all()for a in arrays.values())
    stream=io.BytesIO();np.savez(stream,**arrays);raw=stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw))as z:
        assert len(z.infolist())==4 and all(i.compress_type==zipfile.ZIP_STORED for i in z.infolist())
    assert payload_used()+len(raw)<=PAYLOAD_CAP,'FULL_ARRAY2MIB_BYTE_REFUSAL'
    with path.open('xb')as f:f.write(raw)
    with np.load(path,allow_pickle=False)as z:
        assert set(z.files)==set(arrays)and all(np.array_equal(z[k],a)for k,a in arrays.items()),'LOCAL_FULL_ARRAY_READBACK'
    return len(raw)
