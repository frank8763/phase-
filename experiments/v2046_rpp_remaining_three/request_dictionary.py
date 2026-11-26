"""Lossless path references only; every current request/map reconstructed exactly."""
import copy,hashlib,json
from messages import encode,decode
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def pack(value,cache):
 if value==dict(close=True):return encode(value)
 assert set(value)=={'request','map','path'};request=copy.deepcopy(value['request']);static=dict(path=copy.deepcopy(value['path']),public_route=request.pop('public_route'));identity=digest(static);z=dict(schema='RPP_STATIC_PATH_REFERENCE_V1',static_id=identity,request=request,map=value['map'])
 if identity not in cache:
  assert len(cache)<128,'RPP_PATH_DICTIONARY_LIMIT';cache[identity]=static;z['static']=static
 else:assert digest(cache[identity])==identity,'RPP_PATH_DICTIONARY_MUTATED'
 return encode(z)
def unpack(line,cache):
 z=decode(line)
 if z==dict(close=True):return z
 assert set(z)in [{'schema','static_id','static','request','map'},{'schema','static_id','request','map'}]and z['schema']=='RPP_STATIC_PATH_REFERENCE_V1','RPP_PATH_FRAME_FIELDS'
 identity=z['static_id']
 if 'static'in z:
  assert set(z['static'])=={'path','public_route'}and digest(z['static'])==identity,'RPP_STATIC_PATH_DIGEST'
  if identity in cache:assert cache[identity]==z['static'],'RPP_STATIC_PATH_OVERRIDE'
  else:assert len(cache)<128,'RPP_PATH_DICTIONARY_LIMIT';cache[identity]=z['static']
 assert identity in cache and digest(cache[identity])==identity,'RPP_UNKNOWN_OR_CHANGED_STATIC_PATH'
 request=copy.deepcopy(z['request']);assert 'public_route'not in request;request['public_route']=copy.deepcopy(cache[identity]['public_route']);return dict(request=request,map=z['map'],path=copy.deepcopy(cache[identity]['path']))
