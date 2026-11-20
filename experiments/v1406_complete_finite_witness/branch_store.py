"""Constant-cost incremental receipts, identical complete branch data format."""
import hashlib
import json
from pathlib import Path


class BranchStore:
    def __init__(self,folder,*,input_sha256,np,atomic):
        self.folder=Path(folder);self.folder.mkdir(exist_ok=False)
        self.identity=input_sha256;self.np=np;self.atomic=atomic;self.rows=[];self.closed=False
        self.journal=(self.folder/'ROWS.jsonl').open('x',buffering=1)

    def append(self,proof,states,ctrl):
        assert not self.closed and proof['input_sha256']==self.identity and proof['complete_native']==200
        assert states.shape==(201,8) and ctrl.shape==(200,4) and self.np.isfinite(states).all()and self.np.isfinite(ctrl).all(), 'INCOMPLETE_BRAKING_BRANCH'
        assert not self.rows or proof['before_native']==self.rows[-1]['proof']['before_native']+1, 'BRANCH_ORIGIN_GAP'
        index=len(self.rows);path=self.folder/('branch%05d.npz'%index);temporary=self.folder/('branch%05d.pending'%index)
        with temporary.open('xb')as stream:self.np.savez_compressed(stream,states=states,ctrl=ctrl)
        temporary.replace(path)
        row=dict(index=index,path=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),proof=proof)
        self.journal.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');self.journal.flush()
        self.rows.append(row)
        self.atomic(self.folder/'PROGRESS.json',dict(input_sha256=self.identity,complete_branches=len(self.rows),last_branch_sha256=row['sha256'],closed=False,complete_branch_native_saved=len(self.rows)*200,nominal_native_not_inferred=True))

    def close(self):
        self.journal.close();self.closed=True
        self.atomic(self.folder/'INDEX.json',dict(input_sha256=self.identity,branches=self.rows,closed=True,complete_branch_native_saved=len(self.rows)*200,nominal_native_not_inferred=True))
