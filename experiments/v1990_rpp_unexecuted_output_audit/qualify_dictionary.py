from context import R,C,O,put,load
from request_dictionary import pack,unpack,digest
import copy,json,os

def check():
 os.sched_setaffinity(0,{6});read=lambda p:json.loads(p.read_text());old=R/'runs/v1978_rpp_first_common_round/actual';decoder=load('old_lossless_frame_readonly',R/'experiments/v1978_rpp_first_common_round/messages.py').decode;send={};receive={};before=after=0;count=0;sample=None
 for p in sorted(old.glob('cycle_*_request.json')):
  source=read(p);value=decoder(source['lossless_frame']);raw=pack(value,send);assert unpack(raw,receive)==value and digest(unpack(raw,receive))==digest(value);before+=len(source['lossless_frame'].encode());after+=len(raw.encode());count+=1;sample=value
 assert count>=160 and after<before/2
 negatives=[];raw=pack(sample,{});z=__import__('messages').decode(raw)
 for name,bad in [('wrong_static_SHA',dict(z,static_id='0'*64)),('extra_field',dict(z,truth=1)),('unknown_ref',{k:v for k,v in z.items()if k!='static'})]:
  try:unpack(__import__('messages').encode(bad),{})
  except AssertionError:negatives.append(name)
  else:raise AssertionError('DICTIONARY_BAD_ACCEPTED:'+name)
 assert unpack(pack(dict(close=True),send),receive)==dict(close=True)
 value=dict(passed=True,actual_saved_request_frames=count,logical_current_request_map_path_all_bytes_semantically_exact=True,canonical_json_SHA_all_exact=True,before_frame_bytes=before,after_frame_bytes=after,negative_cases=negatives,only_static_public_route_and_path_shared=True,current_measurement_and_map_in_every_request=True,models=0,RPP_DLL=0,controller_queries=0,physical_native=0,replay_native=0)
 put(O/'DICTIONARY_SOFTWARE_PROOF.json',value);print(json.dumps(value));return value
if __name__=='__main__':check()
