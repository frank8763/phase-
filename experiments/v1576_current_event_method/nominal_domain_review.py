"""New static endpoint-domain review of one exposed saved nominal DATA record.

No old worker/Reader/qualification/audit is called. Decode only stored state
bytes with stdlib; no NumPy, model, policy, FFI, controls or physical execution.
This is not a current-input certificate and cannot grant or tune a method.
"""
import ast
import hashlib
import importlib.abc
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import struct
import sys
import time
import traceback
import lzma
import zipfile
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
STREAM=R/'runs/v1571_complete_batch_comparison/model/audit/WITNESSES.bin'
EXPECTED='81179fd82ad9652472a9e10a44772732b7c03eb43f8264d3c6270824f3fc5b37'
HEADER=struct.Struct('>8sII')


def main():
    start=time.monotonic();assert sorted(os.sched_getaffinity(0))==[4]and os.environ.get('PHASE_REPO')==str(R)
    with(O/'NOMINAL_DOMAIN_REVIEW_ONCE.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
    os.environ.update(MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    s=importlib.util.spec_from_file_location('v1576_domain_review_guard',R/'experiments/v1504_priest_namespace_worker/common.py')
    g=importlib.util.module_from_spec(s);s.loader.exec_module(g);g.guard(O)
    class NoModels(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','mujoco','jax','jaxlib','torch','rclpy','runtime','bindings','kernel','vehicle','factory'}:
                raise AssertionError('STATIC_SAVED_ENDPOINT_ONLY:'+name)
    sys.meta_path.insert(0,NoModels())
    def profile(frame,event,arg):
        if event=='call':
            assert time.monotonic()-start<60
            p=Path(frame.f_code.co_filename)
            if p.is_absolute()and p.is_relative_to(R):
                assert frame.f_code.co_name not in {'step','select','simulate','compute','initial','load_definitions','predict','run','advance'}
                if frame.f_code.co_name=='__init__':assert p==Path(__file__)
    sys.setprofile(profile)
    result=dict(closed=False,passed=False,models=0,native=0,physical_native=0,replay_native=0,
        closed_old_targets_rerun=False,saved_exposed_input_only=True,current_input_qualification=False,
        control_arrays_decoded=False,old_certificate_recomputed=False)
    try:
        h=hashlib.sha256()
        with STREAM.open('rb')as f:
            for b in iter(lambda:f.read(1024**2),b''):h.update(b)
        assert h.hexdigest()==EXPECTED
        nominal=None
        with STREAM.open('rb')as f:
            while True:
                raw=f.read(HEADER.size)
                if not raw:break
                assert len(raw)==HEADER.size
                magic,mlen,plen=HEADER.unpack(raw)
                assert magic==b'WE13XL01'and mlen<=16384 and plen<=8*1024**2
                meta=json.loads(f.read(mlen))
                if meta['kind']=='DATA'and meta['name']=='nominal':
                    assert nominal is None
                    payload=f.read(plen);assert hashlib.sha256(payload).hexdigest()==meta['payload_sha256']
                    nominal=(meta,payload)
                else:f.seek(plen,1)
        assert nominal is not None
        meta,payload=nominal;desc=meta['arrays']['states']
        assert desc['dtype']=='float64'and desc['shape']==[13601,8]
        decoder=lzma.LZMADecompressor(memlimit=64*1024**2)
        raw=decoder.decompress(payload,max_length=6*1024**2)
        assert decoder.eof and not decoder.unused_data
        with zipfile.ZipFile(io.BytesIO(raw))as archive:data=archive.read('states.npy')
        assert data[:6]==b'\x93NUMPY'
        major,minor=data[6:8]
        assert (major,minor)in ((1,0),(2,0))
        nbytes=2 if major==1 else 4;hlen=int.from_bytes(data[8:8+nbytes],'little')
        info=ast.literal_eval(data[8+nbytes:8+nbytes+hlen].decode('latin1'))
        assert info==dict(descr='|u1',fortran_order=False,shape=(8,13601*8))
        values=memoryview(data)[8+nbytes+hlen:];width=13601*8;assert len(values)==8*width
        recovered=bytearray(13601*64);words=[0]*8
        for row in range(13601):
            for column in range(8):
                index=row*8+column
                delta=sum(int(values[plane*width+index])<<(8*plane)for plane in range(8))
                words[column]^=delta
                struct.pack_into('<Q',recovered,index*8,words[column])
        assert hashlib.sha256(recovered).hexdigest()==desc['byte_sha256']
        first=list(struct.unpack_from('<8d',recovered,0));last=list(struct.unpack_from('<8d',recovered,13600*64))
        source=json.loads((R/'runs/v1574_current_owner_capture/SOURCE_INPUT.json').read_text())
        target=source['request']['next_segment']['poses'][-1]
        rear=[last[0]-.3*math.cos(last[2]),last[1]-.3*math.sin(last[2]),last[2]]
        distance=math.dist(rear[:2],target[:2]);angle=abs(math.atan2(math.sin(last[2]-target[2]),math.cos(last[2]-target[2])))
        result.update(passed=True,saved_nominal_first_state=first,saved_nominal_last_state=last,
            saved_nominal_rear_endpoint=rear,original_saved_next_segment_endpoint=target,
            saved_input_segment_endpoint_gate=distance<=.12+1e-8 and angle<=.20+1e-8,
            rear_endpoint_error_m=distance,heading_endpoint_error_rad=angle,
            source_stream_sha256=EXPECTED,stored_state_bytes_sha256=desc['byte_sha256'],
            source_input_file_sha256=hashlib.sha256((R/'runs/v1574_current_owner_capture/SOURCE_INPUT.json').read_bytes()).hexdigest(),
            scope='SAVED_EXPOSED_ENDPOINT_DOMAIN_COMPATIBILITY_NOT_NEW_MODEL_AUDIT',
            future_current_state_outcome_unknown=True,no_parameter_or_gate_change_permitted=True)
    except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);result.update(closed=True,wall_s=time.monotonic()-start)
        (O/'NOMINAL_DOMAIN_REVIEW.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print(json.dumps(result,allow_nan=False))
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
