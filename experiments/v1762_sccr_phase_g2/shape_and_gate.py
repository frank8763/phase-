"""Separately named PhaseG2 geometry; no optimizer/plant is imported by this module."""
import math,copy
CAP=.42722137342572125
WHEELBASE=.6

def interpolate(points,fraction):
 lengths=[math.dist(a,b)for a,b in zip(points,points[1:])];total=sum(lengths);assert total>1e-6 and min(lengths)>1e-8
 target=fraction*total;traversed=0.
 for a,b,d in zip(points,points[1:],lengths):
  if target<=traversed+d:
   f=(target-traversed)/d;return [a[j]+f*(b[j]-a[j])for j in range(2)]
  traversed+=d
 return list(points[-1])

def control_polygon(segment,signed_offset,shoulder):
 assert len(segment)>=6 and all(len(p)==2 and all(math.isfinite(x)for x in p)for p in segment),'INVALID_PUBLIC_SEGMENT'
 assert math.isfinite(signed_offset)and .40<=shoulder<=1.,'UNCHANGED_SHOULDER_BOUNDS'
 lengths=[math.dist(a,b)for a,b in zip(segment,segment[1:])];total=sum(lengths);assert min(lengths)>1e-8
 ta=[(segment[1][j]-segment[0][j])/lengths[0]for j in range(2)];tb=[(segment[-1][j]-segment[-2][j])/lengths[-1]for j in range(2)]
 # Three collinear controls at each clamped cubic endpoint => endpoint tangent
 # equals declared baseline tangent and endpoint geometric curvature is zero.
 d=(.08+.07*shoulder)*total
 before=interpolate(segment,.475);after=interpolate(segment,.525);t=[after[j]-before[j]for j in range(2)];norm=math.hypot(*t);assert norm>1e-8
 mid=interpolate(segment,.5);normal=[-t[1]/norm,t[0]/norm]
 out=[list(segment[0]),[segment[0][j]+d*ta[j]for j in range(2)],[segment[0][j]+2*d*ta[j]for j in range(2)],[mid[j]+signed_offset*normal[j]for j in range(2)],[segment[-1][j]-2*d*tb[j]for j in range(2)],[segment[-1][j]-d*tb[j]for j in range(2)],list(segment[-1])]
 assert all(math.isfinite(x)for p in out for x in p);return out

def full_path_gate(path,origin_yaw):
 assert len(path)>=3 and all(len(p)==2 and all(math.isfinite(x)for x in p)for p in path),'INVALID_FULL_PATH'
 lengths=[];headings=[]
 for a,b in zip(path,path[1:]):
  d=math.dist(a,b);assert d>1e-8,'DEGENERATE_FULL_PATH';lengths.append(d);headings.append(math.atan2(b[1]-a[1],b[0]-a[0]))
 worst=0.;max_turn=0.
 for i in range(1,len(path)-1):
  a=[path[i][j]-path[i-1][j]for j in range(2)];b=[path[i+1][j]-path[i][j]for j in range(2)];chord=math.hypot(a[0]+b[0],a[1]+b[1]);assert chord>1e-8,'PATH_REVERSAL'
  k=2*(a[0]*b[1]-a[1]*b[0])/(lengths[i-1]*lengths[i]*chord);worst=max(worst,abs(math.atan(WHEELBASE*k)))
  max_turn=max(max_turn,abs(math.atan2(math.sin(headings[i]-headings[i-1]),math.cos(headings[i]-headings[i-1]))))
 first_error=abs(math.atan2(math.sin(headings[0]-origin_yaw),math.cos(headings[0]-origin_yaw)))
 checks=dict(sampled_center_steering=worst<=CAP,whole_path_heading_increment=max_turn<=.24,initial_reference_heading_match=first_error<=.035)
 return dict(passed=all(checks.values()),checks=checks,max_abs_sampled_center_steering_rad=worst,original_center_cap_rad=CAP,max_full_path_heading_delta_rad=max_turn,initial_path_heading_error_rad=first_error,sampled_only_no_physical_certificate=True)

def endpoint_residuals(p):
 def cross(a,b):return a[0]*b[1]-a[1]*b[0]
 a=[p[1][j]-p[0][j]for j in range(2)];b=[p[2][j]-p[1][j]for j in range(2)];c=[p[-2][j]-p[-3][j]for j in range(2)];d=[p[-1][j]-p[-2][j]for j in range(2)]
 return [cross(a,b),cross(c,d)]

def qualify():
 straight=[[i/10.,0.]for i in range(11)]
 for side in [-1.,1.]:
  for shoulder in [.4,.55,.75,.92,1.]:
   p=control_polygon(straight,side*.5,shoulder);assert p[0]==straight[0]and p[-1]==straight[-1]and max(abs(x)for x in endpoint_residuals(p))<1e-12 and (p[3][1]>0)==(side>0)
 assert full_path_gate(straight,0.)['passed']
 cases=[([[0.,0.],[.1,0.],[.1,.1]],0.),(straight,1.),([[0.,0.],[0.,0.],[1.,0.]],0.),([[0.,0.],[1.,0.],[0.,0.]],0.),([[0.,0.],[float('nan'),0.],[1.,0.]],0.)]
 for path,yaw in cases:
  try:passed=full_path_gate(path,yaw)['passed']
  except AssertionError:passed=False
  assert not passed,'NEW_FILTER_ACCEPTED_BAD_PATH'
 return dict(endpoint_software_cases=10,new_filter_negative_cases=len(cases),source_only_no_numerical_queries=True)
