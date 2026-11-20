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
