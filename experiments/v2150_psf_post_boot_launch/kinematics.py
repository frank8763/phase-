"""Explicit ideal speed-curvature fixture. No Phase model or solver imports."""
import math
N=8;DT=.1;KMAX=1/1.32
def rollout_jac(z,x0,gear):
 assert gear in(-1,1)and len(z)==2*N and len(x0)==3
 x=list(map(float,x0));J=[[0.]*16 for _ in range(3)];states=[x[:]];jacs=[[r[:]for r in J]]
 for i in range(N):
  s,k=z[2*i:2*i+2];v=gear*s;yaw=x[2];co,si=math.cos(yaw),math.sin(yaw)
  a=DT*v;new=[[J[0][j]-a*si*J[2][j]for j in range(16)],[J[1][j]+a*co*J[2][j]for j in range(16)],J[2][:]]
  new[0][2*i]+=DT*gear*co;new[1][2*i]+=DT*gear*si
  new[2][2*i]+=DT*gear*k;new[2][2*i+1]+=DT*v
  x=[x[0]+a*co,x[1]+a*si,x[2]+DT*v*k];J=new
  states.append(x[:]);jacs.append([r[:]for r in J])
 return states,jacs