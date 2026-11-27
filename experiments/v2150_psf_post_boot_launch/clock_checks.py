"""Saved real fresh receipts, pure builder/decoder test in original runtime."""
from pathlib import Path
import sys,json,copy
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;P=R/'experiments/v2128_filter_segment_wire';sys.path.insert(0,str(C))
from context import read,load,sha
source=read(R/'runs/v2128_filter_segment_wire/SOURCE_FREEZE.json')['files'];old_source=dict(source)
for p in C.glob('*.py'):source[str(p.relative_to(R))]=sha(p)
old_builder=load('original_current_builder',P/'current_request.py');old_decoder=load('original_clock_decoder',P/'peer_contract.py')
new_builder=load('draft_preserved_clock_builder',C/'current_request.py');new_decoder=load('draft_preserved_clock_decoder',C/'peer_contract.py')
O=R/'runs/v2128_filter_segment_wire/components/PSF/actual';rows=[];raw=lambda z:json.dumps(z,allow_nan=False).encode()+b'\n'
for sequence in range(3):
 receipt=read(O/f'cycle_{sequence:06d}_origin.json')['receipt'];selected=read(O/f'FILTER_QUERY_{sequence:03d}_ROUTE.json')['selected'];saved=read(O/f'FILTER_QUERY_{sequence:03d}_INPUT.json');runid=saved['current']['run_id']
 original=saved # exact immutable V2128 frame; production new builder is separately exercised below
 if sequence==2:
  try:old_decoder.decode(raw(original),sequence,'PSF',runid)
  except AssertionError:pass
  else:raise AssertionError('ORIGINAL_FLOAT_CLOCK_BUG_NOT_REPRODUCED')
 else:old_decoder.decode(raw(original),sequence,'PSF',runid)
 fixed=new_builder.build(None,receipt,None,selected,source,run_id=runid);new_decoder.decode(raw(fixed),sequence,'PSF',runid,last_native=None if sequence==0 else sequence*5-5)
 assert fixed['request']['case']['sim_time']==fixed['request']['origin_sim_time']==receipt['packet']['sim_time']
 assert fixed['current']['pose']==original['current']['pose']and fixed['current']['sim_time']==original['current']['sim_time']and fixed['current']['nominal_twist']==original['current']['nominal_twist']
 rows.append(dict(sequence=sequence,native=receipt['packet']['native_tick'],measured_time=receipt['packet']['sim_time'],recomputed_time=.01*receipt['packet']['native_tick'],difference_s=.01*receipt['packet']['native_tick']-receipt['packet']['sim_time']))
# Synthetic decoder-only adjacent-float clocks, explicitly no observation/plant authority.
import math
from context import digest
synthetic=0
for sequence in range(20):
 canonical=.05*sequence;clocks=[0.]if sequence==0 else[canonical,math.nextafter(canonical,-math.inf),math.nextafter(canonical,math.inf)]
 for clock in clocks:
  z=copy.deepcopy(fixed);z['current'].update(native=5*sequence,sim_time=clock);z['current'].pop('input_sha256');z['current']['input_sha256']=digest(z['current'])
  z['request'].update(origin_native=5*sequence,origin_sim_time=clock,input_sha256=z['current']['input_sha256']);z['request']['case']['sim_time']=clock;z['request'].pop('request_sha256');z['request']['request_sha256']=digest(z['request'])
  new_decoder.decode(raw(z),sequence,'PSF',runid,last_native=None if sequence==0 else sequence*5-5);synthetic+=1
negatives=[]
for name,seq,method in [('stale_sequence',1,'PSF'),('foreign_method',2,'PCBF')]:
 try:new_decoder.decode(raw(fixed),seq,method,runid)
 except AssertionError:negatives.append(name)
 else:raise AssertionError(name)
bad=copy.deepcopy(fixed);bad['request']['origin_sim_time']+=1e-4
try:new_decoder.decode(raw(bad),2,'PSF',runid)
except AssertionError:negatives.append('changed_clock_or_digest')
else:raise AssertionError('CLOCK_TAMPER_ACCEPTED')
print(json.dumps(dict(passed=True,old_real_third_frame_failure_reproduced=True,exact_measured_clock_preserved=True,original_native_clock_tolerance=1e-8,rows=rows,synthetic_decoder_only_clock_cases=synthetic,negative_cases=negatives,models=0,optimizer_queries=0,physical_native=0,production_builder_decoder=True,source_sha256={str(p.relative_to(R)):sha(p)for p in[C/'clock_checks.py',C/'current_request.py',C/'peer_contract.py']})))
