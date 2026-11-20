"""Atomic per-origin branch evidence with an exact journal and content hashes."""
import hashlib
import json
from pathlib import Path


class BranchStore:
    def __init__(self,folder,*,input_sha256,np,atomic):
        self.folder=Path(folder);self.folder.mkdir(exist_ok=False)
        self.identity=input_sha256;self.np=np;self.atomic=atomic;self.rows=[];self.closed=False

    def append(self,proof,states,ctrl):
        assert not self.closed and proof['input_sha256']==self.identity and proof['complete_native']==200
        assert states.shape==(201,8) and ctrl.shape==(200,4) and self.np.isfinite(states).all()and self.np.isfinite(ctrl).all(), 'INCOMPLETE_BRAKING_BRANCH'
        assert not self.rows or proof['before_native']==self.rows[-1]['proof']['before_native']+1, 'BRANCH_ORIGIN_GAP'
        index=len(self.rows);path=self.folder/('branch%05d.npz'%index);temporary=self.folder/('branch%05d.pending'%index)
        with temporary.open('xb')as stream:self.np.savez_compressed(stream,states=states,ctrl=ctrl)
        temporary.replace(path)
        row=dict(index=index,path=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),proof=proof)
        self.rows.append(row)
        self.atomic(self.folder/'INDEX.json',dict(input_sha256=self.identity,branches=self.rows,closed=False,complete_branch_native_saved=len(self.rows)*200,nominal_native_not_inferred=True))

    def close(self):
        self.closed=True
        self.atomic(self.folder/'INDEX.json',dict(input_sha256=self.identity,branches=self.rows,closed=True,complete_branch_native_saved=len(self.rows)*200,nominal_native_not_inferred=True))


def verified_branch(folder,row,np):
    path=Path(folder)/row['path'];assert Path(row['path']).name==row['path'] and not path.is_symlink()
    assert path.stat().st_size==row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'], 'BRANCH_EVIDENCE_CHANGED'
    with np.load(path,allow_pickle=False)as value:
        assert set(value.files)=={'states','ctrl'}
        states=value['states'].copy();ctrl=value['ctrl'].copy()
    assert states.shape==(201,8) and ctrl.shape==(200,4) and np.isfinite(states).all()and np.isfinite(ctrl).all()
    return states,ctrl
