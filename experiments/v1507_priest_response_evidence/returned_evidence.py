"""Save full returned nominal and partial arrays without truncating unknown prefixes."""
import importlib.util
import io
from pathlib import Path
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1507_exact_branch_serialization',C/'branch_store.py');codec=importlib.util.module_from_spec(s);s.loader.exec_module(codec)

def save_returned(output,result,arrays,*,writer,boundary):
 import numpy as np
 output=codec.metered(output,writer,boundary);nominal={name:np.asarray(arrays[name],dtype=np.float64)for name in ['states','ctrl','memory']}
 partial=arrays.get('partial_branch');partial_meta=None
 if partial is not None:
  nominal['partial_branch_states']=np.asarray(partial['states'],dtype=np.float64);nominal['partial_branch_ctrl']=np.asarray(partial['ctrl'],dtype=np.float64);partial_meta={k:v for k,v in partial.items()if k not in {'states','ctrl'}};partial_meta.update(saved_states=len(partial['states']),saved_ctrl=len(partial['ctrl']),no_missing_suffix_invented=True)
 buffer=io.BytesIO();np.savez_compressed(buffer,**nominal);payload=buffer.getvalue();assert len(payload)<=1024**2
 journal=codec.encoded(dict(journal=arrays['journal'],modes=arrays['modes'],partial_branch=partial_meta,saved_array_shapes={k:list(v.shape)for k,v in nominal.items()},generation=result,full_Nplus1=len(arrays['states'])==len(arrays['ctrl'])+1,unknowns_preserved=True));assert len(journal)<=3*1024**2
 codec.write_atomic(output/'RETURNED_ARRAYS.npz',payload,writer);codec.write_atomic(output/'RETURNED_JOURNAL.json',journal,writer)
 receipt=dict(array_bytes=len(payload),arrays_sha256=codec.sha(payload),journal_bytes=len(journal),journal_sha256=codec.sha(journal),partial_branch_present=partial is not None,generation_passed=bool(result['passed']),storage_not_scientific_pass=True)
 codec.write_atomic(output/'RETURNED_RECEIPT.json',codec.encoded(receipt),writer);return receipt
