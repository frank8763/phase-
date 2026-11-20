"""Reject malformed HTTP range/asset responses without making network calls."""
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import resume as m
original=m.O
rejected=[]
for label,status,span,payload,digest in [
 ('ignored_range','200','bytes 0-3/4',b'abcd',hashlib.sha256(b'abcd').hexdigest()),
 ('wrong_range_start','206','bytes 1-4/4',b'abcd',hashlib.sha256(b'abcd').hexdigest()),
 ('wrong_total','206','bytes 0-3/5',b'abcd',hashlib.sha256(b'abcd').hexdigest()),
 ('oversized_range','206','bytes 0-3/4',b'abcde',hashlib.sha256(b'abcd').hexdigest()),
 ('full_asset_wrong_SHA','206','bytes 0-3/4',b'abcd','0'*64)]:
 m.O=original/'contract_fixtures'/label;m.O.mkdir(parents=True)
 row=dict(name='fixture.part000',size=4,digest='sha256:'+digest,browser_download_url='https://example.invalid/never-called')
 def response(command,**kwargs):
  Path(command[command.index('--dump-header')+1]).write_text('HTTP/1.1 '+status+' fixture\r\nContent-Range: '+span+'\r\n\r\n')
  Path(command[command.index('--output')+1]).write_bytes(payload)
  return SimpleNamespace(returncode=0,stdout=status)
 try:
  with patch.object(m.subprocess,'run',response):m.download(m.O/'download',row)
 except AssertionError:rejected.append(label)
 else:raise AssertionError('MALFORMED_RANGE_ACCEPTED '+label)
m.O=original
m.dump(original/'NEGATIVE_QUALIFICATION.json',dict(passed=True,negative_cases=rejected,network_calls=0,models=0))
print(rejected)

# A transient TLS handshake failure is retried with TLS verification intact;
# malformed content is still an immediate refusal.
for label,always_fail in [('TLS_then_valid_range',False),('TLS_retry_exhaustion',True)]:
 m.O=original/'contract_fixtures'/label;m.O.mkdir(parents=True);calls=[0]
 row=dict(name='fixture.part000',size=4,digest='sha256:'+hashlib.sha256(b'abcd').hexdigest(),browser_download_url='https://example.invalid/never-called')
 def response(command,**kwargs):
  calls[0]+=1;fail=always_fail or calls[0]==1
  Path(command[command.index('--dump-header')+1]).write_text('' if fail else 'HTTP/1.1 206 fixture\r\nContent-Range: bytes 0-3/4\r\n\r\n')
  Path(command[command.index('--output')+1]).write_bytes(b'' if fail else b'abcd')
  return SimpleNamespace(returncode=35 if fail else 0,stdout='000' if fail else '206')
 try:
  with patch.object(m.subprocess,'run',response),patch.object(m.time,'sleep',lambda _:None):m.download(m.O/'download',row)
 except AssertionError:
  assert always_fail and calls[0]==4;rejected.append('bounded_TLS_retry_exhaustion')
 else:assert not always_fail and calls[0]==2 and (m.O/'download').read_bytes()==b'abcd'
m.O=original;m.dump(original/'NEGATIVE_QUALIFICATION.json',dict(passed=True,negative_cases=rejected,transient_TLS_then_valid_range_passed=True,network_calls=0,models=0));print('TLS transient retry and finite exhaustion passed')
