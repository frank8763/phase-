"""PSF equation5 / PCBF equation9 on an explicit illustrative linear system.

This is a formulation solver, not the Phase vehicle model or a safety guarantee.
"""
def solve(np,linprog,*,kind,x0,nominal,N=8):
 assert kind in {'PSF','PCBF'}and type(N)is int and N==8
 # z=[u(0:N),x(0:N+1),abs(u0-up),xi(0:N),xi_terminal]
 t=2*N+1;slack=t+1;terminal=slack+N;size=terminal+1
 Aeq=[];beq=[];A=[];b=[]
 row=np.zeros(size);row[N]=1;Aeq.append(row);beq.append(x0)
 for i in range(N):
  row=np.zeros(size);row[N+i+1]=1;row[N+i]=-1;row[i]=-1;Aeq.append(row);beq.append(0.)
  delta=0.01*i if kind=='PCBF'else 0.
  for sign in [-1.,1.]:
   row=np.zeros(size);row[N+i]=sign;row[slack+i]=-1;A.append(row);b.append(1.-delta)
 for sign in [-1.,1.]:
  row=np.zeros(size);row[2*N]=sign;row[terminal]=-1;A.append(row);b.append(.25)
  row=np.zeros(size);row[0]=sign;row[t]=-1;A.append(row);b.append(sign*nominal)
 bounds=[(-.25,.25)]*N+[(None,None)]*(N+1)+[(0,None)]+([(0,None)]*(N+1)if kind=='PCBF'else[(0,0)]*(N+1))
 options=dict(maxiter=10000,threads=1,parallel=False)
 soft=None;value=None
 if kind=='PCBF':
  c=np.zeros(size);c[slack:terminal]=1;c[terminal]=100
  soft=linprog(c,A_ub=A,b_ub=b,A_eq=Aeq,b_eq=beq,bounds=bounds,method='highs',options=options)
  assert soft.success,'PCBF_AUXILIARY_LP_FAILED';value=float(c@soft.x)
  # The separate performance problem fixes the auxiliary optimal slacks.
  bounds[-(N+1):]=[(float(v),float(v))for v in soft.x[slack:]]
 c=np.zeros(size);c[t]=1;solution=linprog(c,A_ub=A,b_ub=b,A_eq=Aeq,b_eq=beq,bounds=bounds,method='highs',options=options)
 if not solution.success:return dict(feasible=False,status=int(solution.status),method=kind,physical_authority=False)
 z=solution.x;eq=float(np.max(abs(np.asarray(Aeq)@z-np.asarray(beq))));ineq=float(np.max(np.asarray(A)@z-np.asarray(b)));assert eq<=1e-8 and ineq<=1e-8
 return dict(feasible=True,method=kind,first_input=float(z[0]),inputs=z[:N].tolist(),states=z[N:2*N+1].tolist(),slacks=z[slack:].tolist(),auxiliary_value=value,objective=float(z[t]),maximum_equality_residual=eq,maximum_inequality_residual=ineq,physical_authority=False,illustrative_linear_system_only=True,Phase_vehicle_safety_qualified=False)
