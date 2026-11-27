"""New geometric PRIEST adaptation; no optimizer, physics or command rescue."""
import math
LOOKAHEAD=.6;SPEED=.08;KMAX=1/1.32
def evaluate(cx,cy,t):
 assert len(cx)==len(cy)==11 and 0<=t<=10 and all(type(v)in(int,float)and math.isfinite(v)for v in cx+cy)
 u=t/10.;return[sum(math.comb(10,i)*u**i*(1-u)**(10-i)*c[i]for i in range(11))for c in[cx,cy]]
def command(cx,cy,*,body,gear,receipt_native,proposal_native):
 assert type(receipt_native)is int and receipt_native==proposal_native,'TRACKER_FOREIGN_OR_STALE_ORIGIN'
 assert len(body)==5 and all(type(v)in(int,float)and math.isfinite(v)for v in body)and gear in(-1,1),'TRACKER_INPUT_DOMAIN'
 rear=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2])]
 points=[evaluate(cx,cy,i*.01)for i in range(1001)]
 assert math.dist(rear,points[0])<=1e-6,'TRACKER_POLYNOMIAL_ORIGIN_MISMATCH'
 target=points[-1];arc=0.;idx=1000
 for i,(a,b)in enumerate(zip(points,points[1:]),1):
  arc+=math.dist(a,b)
  if arc>=LOOKAHEAD:target=b;idx=i;break
 dx,dy=target[0]-rear[0],target[1]-rear[1];co,si=math.cos(body[2]),math.sin(body[2]);localx=co*dx+si*dy;localy=-si*dx+co*dy;r2=dx*dx+dy*dy
 if r2<=.01**2:return dict(request=[0.,0.,False],endpoint_hold=True,component_only=True,physical_admission=False)
 assert gear*localx>0,'TRACKER_TARGET_OPPOSES_GEAR'
 curvature=2*localy/r2;v=gear*SPEED;w=v*curvature
 assert abs(w)<=abs(v)*KMAX+1e-6,'TRACKER_CURVATURE_DOMAIN_REFUSED'
 return dict(request=[v,w,False],lookahead_arc_m=arc,target_time_s=idx*.01,target=target,curvature_m_inv=curvature,component_only=True,physical_admission=False,adaptation='PRIEST_POLYNOMIAL_GEOMETRIC_PP_0P6_SPEED_0P08',polynomial_timing_preserved=False,complete_response_still_required=True)
