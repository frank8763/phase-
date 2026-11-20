"""Roundtrip every retained actual V1396 branch; zero model computation."""
import copy
import hashlib
import json
import os
from pathlib import Path
import time
import zlib
from stream import BranchStore,BranchReader,sha,MAGIC,HEADER

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def atomic(path,value):
    p=Path(path);temporary=p.with_suffix(p.suffix+'.tmp');temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(p)


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O.mkdir(exist_ok=False)
    import numpy as np
    source=R/'runs/v858_nav2_verified/v1396/full9390_main/BRAKING_ALTERNATIVES.npz';source_sha=sha(source)
    atomic(O/'CLAIM.json',dict(started_unix=time.time(),input=str(source.relative_to(R)),input_sha256=source_sha,models=0,not_rerunning_any_old_model=True))
    negative=[]
    def reject(name,fn):
        try:fn()
        except (AssertionError,EOFError,zlib.error):negative.append(name)
        else:raise AssertionError('CORRUPT_BRANCH_STORAGE_ACCEPTED:'+name)
    started=time.monotonic()
    with np.load(source,allow_pickle=False)as z:
        states=z['states'];ctrl=z['ctrl'];assert states.shape==(2585,201,8)and ctrl.shape==(2585,200,4)
        store=BranchStore(O/'roundtrip',input_sha256=source_sha,np=np,atomic=atomic,maximum_branches=2585)
        reject('incomplete201_states',lambda:store.append(dict(input_sha256=source_sha,complete_native=200,before_native=10775),states[0,:-1],ctrl[0]))
        reject('float32_precision_change',lambda:store.append(dict(input_sha256=source_sha,complete_native=200,before_native=10775),states[0].astype(np.float32),ctrl[0].astype(np.float32)))
        for i in range(len(states)):
            proof=dict(input_sha256=source_sha,complete_native=200,before_native=10775+i,qualification_source_is_saved_actual_branch=True)
            store.append(proof,states[i],ctrl[i])
        store.close();index=json.loads((store.folder/'INDEX.json').read_text());reader=BranchReader(store.folder,index,np)
        for i,row in enumerate(index['branches']):
            a,b=reader.read(row)
            assert a.astype('<f8',copy=False).tobytes()==states[i].astype('<f8',copy=False).tobytes()and b.astype('<f8',copy=False).tobytes()==ctrl[i].astype('<f8',copy=False).tobytes(), 'IEEE754_BITS_CHANGED'
        reader.finish()
        reader=BranchReader(store.folder,index,np)
        reject('wrong_frame_order',lambda:reader.read(dict(index['branches'][0],index=1)));reader.stream.close()
        altered=copy.deepcopy(index);altered['branches'][0]['raw_sha256']='0'*64;reader=BranchReader(store.folder,altered,np)
        reject('wrong_raw_frame_SHA',lambda:reader.read(altered['branches'][0]));reader.stream.close()
        altered=copy.deepcopy(index);altered['frame_file_sha256']='0'*64
        reject('changed_whole_stream_SHA',lambda:BranchReader(store.folder,altered,np))
        # A valid gzip containing one altered XOR payload must still fail the
        # independent raw frame SHA, even with a matching outer stream SHA.
        import gzip
        first=states[0].astype('<f8',copy=False).tobytes()+ctrl[0].astype('<f8',copy=False).tobytes();changed=bytearray(first);changed[0]^=1
        row=index['branches'][0];payload=MAGIC+HEADER.pack(0,len(first),bytes.fromhex(row['raw_sha256']))+bytes(changed)
        damaged=store.folder/'altered_payload.gz';damaged.write_bytes(gzip.compress(payload,mtime=0))
        altered=dict(index,frame_file=damaged.name,frame_file_sha256=sha(damaged),frame_file_bytes=damaged.stat().st_size,branches=[row]);reader=BranchReader(store.folder,altered,np)
        reject('changed_XOR_payload',lambda:reader.read(row));reader.stream.close();damaged.unlink()
        streamed=index['frame_file_bytes'];original=source.stat().st_size
        # Compare actual per-origin NPZ representation on64 real branches,
        # only as an estimate. This temporary benchmark is removed afterward.
        import io
        separate=0
        for i in range(64):
            buffer=io.BytesIO();np.savez_compressed(buffer,states=states[i],ctrl=ctrl[i]);separate+=len(buffer.getvalue())
        raw_bytes=states.nbytes+ctrl.nbytes
    assert sha(source)==source_sha
    result=dict(passed=True,source=str(source.relative_to(R)),source_sha256=source_sha,saved_actual_branches_roundtripped=2585,
                each_branch_states=201,each_branch_ctrl=200,every_float64_bit_and_raw_SHA_exact=True,stream_SHA_and_gzip_CRC_passed=True,
                original_npz_bytes=original,stream_bytes=streamed,raw_bytes=raw_bytes,stream_ratio_to_original_npz=streamed/original,
                separate_npz64_bytes=separate,estimated_separate_npz2585_bytes=separate/64*2585,
                negative_cases=negative,wall_s=time.monotonic()-started,models=0,analytical_native=0,physical_native=0,replay_native=0,
                not_new_actual_or_modeled_trajectory=True,physical_admission=False)
    atomic(O/'QUALIFICATION.json',result)
    files=[C/'stream.py',C/'qualify.py',C/'PROTOCOL.md'];atomic(O/'SOURCE_FREEZE.json',dict(files={str(p.relative_to(R)):sha(p)for p in files},qualification='runs/v1407_lossless_branch_stream/QUALIFICATION.json',models=0,physical_admission=False))
    print(json.dumps(result))


if __name__=='__main__':main()
