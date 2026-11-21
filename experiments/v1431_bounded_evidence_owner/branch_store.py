"""Original lossless branch stream with explicit write and final-index budget."""
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1431_original_lossless_branch_stream',R/'experiments/v1407_lossless_branch_stream/stream.py');original=importlib.util.module_from_spec(s);s.loader.exec_module(original)

class BranchStore(original.BranchStore):
 def __init__(self,folder,*,input_sha256,np,atomic,maximum_branches,quota):
  self.quota=quota;self.pending_index_bytes=4096;self.hold_key="branch-index:"+str(Path(folder).resolve())
  quota.hold(self.hold_key,2*self.pending_index_bytes+32768)
  quota.admit(32*1024,'OPEN_COMPLETE_BRANCH_STREAM')
  super().__init__(folder,input_sha256=input_sha256,np=np,atomic=atomic,maximum_branches=maximum_branches)

 def append(self,proof,states,ctrl):
  # Exact row/index upper bound includes the full proof. Compression is never
  # assumed to save space, and the original frame precision/schema is retained.
  row=dict(index=len(self.rows),frame_bytes=original.FRAME_BYTES,raw_sha256='0'*64,proof=proof)
  row_bytes=4*len(json.dumps(row,indent=2,allow_nan=False).encode())+2048
  pending=self.pending_index_bytes+row_bytes
  self.quota.hold(self.hold_key,2*pending+32768)
  self.quota.admit(original.FRAME_BYTES+original.HEADER.size+1024+row_bytes+32*1024,'APPEND_COMPLETE_201_STATE_200_CONTROL_BRANCH')
  super().append(proof,states,ctrl);self.pending_index_bytes=pending

 def close(self):
  if self.closed:return
  with self.quota.spend(self.hold_key):
   self.quota.admit(2*self.pending_index_bytes+32*1024,'FINALIZE_COMPLETE_BRANCH_STREAM_AND_INDEX')
   super().close()
  self.quota.release(self.hold_key)
