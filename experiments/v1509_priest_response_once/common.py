"""Exact immutable source/input composition and bounded metadata primitives."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
BASE=R/'runs/v1507_priest_response_evidence/SOURCE_FREEZE.json'
INPUT=R/'runs/v1504_priest_namespace_worker/numeric/CURRENT_INPUT.json'
PROPOSAL=R/'runs/v1504_priest_namespace_worker/SAVED_OPTIMIZER_PROPOSAL.json'
SETUP=R/'runs/v1497_priest_complete_response/saved_input/SETUP.json'
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as stream:
  for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
 return h.hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def put(path,value,maximum=65536):
 raw=json.dumps(value,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<=maximum,'RESPONSE_METADATA_BYTE_BOUND';temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_bytes(raw);temporary.replace(path)
def sources():
 spec=read(O/'SOURCE_FREEZE.json');assert spec['base_manifest_sha256']==sha(BASE)
 values=read(BASE)['files'].copy()
 for n,h in spec['files'].items():
  assert n not in values or values[n]==h;values[n]=h
 assert all(sha(R/n)==h for n,h in values.items()),'RESPONSE_FROZEN_SOURCE_CHANGED'
 return values
def inputs():
 fixed=read(O/'FIXED_INPUTS.json')
 for p,k in [(INPUT,'input_file_sha256'),(PROPOSAL,'proposal_file_sha256'),(SETUP,'setup_file_sha256')]:assert sha(p)==fixed[k]
 current=read(INPUT);proposal=read(PROPOSAL)['candidate'];setup=read(SETUP)
 assert current['input_sha256']==fixed['input_sha256']and proposal['proposal_sha256']==fixed['proposal_sha256']and proposal['input_sha256']==current['input_sha256']
 return current,proposal,setup
def limits():return read(C/'LIMITS.json')
def guard():return load('v1509_immutable_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
def usage():
 seen=set();total=0
 for root,ds,fs in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in fs]:
   st=p.lstat();key=(st.st_dev,st.st_ino)
   if key not in seen:seen.add(key);total+=st.st_blocks*512
 return total
