"""Initial equality and declared obstacle inequalities must agree before solve."""
import json,hashlib,math

def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def inspect_request(request,*,expected_sha256,expected_author_sha256):
 assert digest(request)==expected_sha256,'PRIEST_REQUEST_IDENTITY'
 clean=dict(request);saved=clean.pop('request_sha256');assert digest(clean)==saved,'PRIEST_INNER_REQUEST_DIGEST'
 assert request['port_identity']['author_sha256']==expected_author_sha256,'PRIEST_AUTHOR_SOURCE'
 state=request['initial_state'];assert len(state)==6 and all(type(x)in(int,float)and math.isfinite(x)for x in state)
 params=request['constructor_kwargs'];a,b=params['a_obs_1'],params['b_obs_1'];assert all(type(x)in(int,float)and math.isfinite(x)and x>0 for x in[a,b])
 points=request['static_points_world'];assert len(points)==params['num_obs_1']and len(points)>0
 x,y=state[:2];values=[]
 for ox,oy in points:
  assert all(type(z)in(int,float)and math.isfinite(z)for z in[ox,oy]);values.append(((x-ox)/a)**2+((y-oy)/b)**2)
 violations=[i for i,v in enumerate(values)if v<1.]
 return dict(mathematical_initial_boundary_compatible=not violations,disposition='INITIAL_INPUT_PREFLIGHT_ONLY'if not violations else'ADAPTER_INITIAL_BOUNDARY_INCOMPATIBLE',initial_obstacle_violations=violations,minimum_normalized_distance_squared=min(values),optimizer_launch_authorized=False,models_authorized=False,physical_authority=False,whole_navigation_passed=False,algorithm_performance_observation=False)
