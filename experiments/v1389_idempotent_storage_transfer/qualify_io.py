"""Meaningful finite network/reconciliation fixtures; no model or network writes."""
import ast
import hashlib
from pathlib import Path
from unittest.mock import patch
import resume as m
original=m.O
checks=[]
for label,failures,expected in [('read_EOF_then_valid',1,2),('read_EOF_exhaustion',9,3),('write_not_blindly_retried',9,1)]:
 m.O=original/'fixtures'/label;m.O.mkdir(parents=True);calls=[0]
 def single(*args,**kwargs):
  calls[0]+=1
  if calls[0]<=failures:raise AssertionError('GITHUB_TRANSFER_FAILED EOF')
  return '[]'
 failed=False
 try:
  with patch.object(m,'_single_gh',single),patch.object(m.time,'sleep',lambda _:None):m.bounded_gh(['api','fixture'] if label.startswith('read_') else ['release','upload','fixture'])
 except AssertionError:failed=True
 assert calls[0]==expected and failed==(label!='read_EOF_then_valid');checks.append(label)
for label,present,bad,expected in [('ambiguous_upload_reconciled',True,False,1),('remote_digest_conflict',True,True,0),('absent_upload_finite',False,False,2)]:
 m.O=original/'fixtures'/label;m.O.mkdir(parents=True);p=m.O/'fixture';p.write_bytes(b'data');calls=[0]
 row=dict(size=4,digest='sha256:'+('0'*64 if bad else hashlib.sha256(b'data').hexdigest()))
 def upload(*args,**kwargs):calls[0]+=1;raise AssertionError('GITHUB_TRANSFER_FAILED EOF')
 failed=False
 try:
  with patch.object(m.base,'gh',upload),patch.object(m,'assets',lambda _: {'fixture':row} if present else {}),patch.object(m.time,'sleep',lambda _:None):m.ensure_uploaded(p,{'fixture':row} if bad else {})
 except AssertionError:failed=True
 assert calls[0]==expected and failed==(label!='ambiguous_upload_reconciled');checks.append(label)
m.O=original
old=ast.parse((m.R/'experiments/v1388_resilient_storage_io/resume.py').read_text());new=ast.parse((m.C/'resume.py').read_text())
for name in ['download','preserve','main','assets']:
 a=next(x for x in old.body if isinstance(x,ast.FunctionDef) and x.name==name);b=next(x for x in new.body if isinstance(x,ast.FunctionDef) and x.name==name);assert ast.dump(a)==ast.dump(b)
m.dump(original/'IO_QUALIFICATION.json',dict(passed=True,checks=checks,unchanged_qualified_range_member_cleanup_code=True,models=0,network_writes=0))
print(checks)
