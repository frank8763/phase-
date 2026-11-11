// Analytical expansion accelerator ONLY. Final admission uses frozen Python.
#include <algorithm>
#include <cmath>
#include <cstring>
static double clip(double x,double l,double h){return std::max(l,std::min(h,x));}
static double inv(double q,int side){double t=std::tan(q);return t/(.6+side*.27*t);}
static double virt(const double *q){return std::atan(.6*(inv(q[0],1)+inv(q[1],-1))/2);}
extern "C" int expand(const double *initial,const double *memory,const double *targets,const double *speeds,int nt,int steps,const double *limits,const double *rates,const double *p,double *states,double *controls,double *memories){
 const double cap=.42722137342572125,maxk=std::tan(cap)/.6;
 for(int action=0;action<nt;++action){
  double s[8],u[4];std::memcpy(s,initial,8*sizeof(double));std::memcpy(u,memory,4*sizeof(double));double integral=memory[4];
  for(int j=0;j<steps;++j){
   const double v=speeds[action];const bool braking=v<.005;double wantedk=std::tan(targets[action])/.6;
   double lower[4],upper[4],rate[4];
   for(int i=0;i<4;++i){rate[i]=rates[i]*.01;lower[i]=std::max(limits[2*i],u[i]-rate[i]);upper[i]=std::min(limits[2*i+1],u[i]+rate[i]);}
   lower[2]=std::max(0.,lower[2]);lower[3]=std::max(0.,lower[3]);
   double pk=(inv(u[0],1)+inv(u[1],-1))/2,delta=std::atan(.6*pk);
   double klo=std::max({-maxk,inv(lower[0],1),inv(lower[1],-1),std::tan(std::max(-cap,delta-.006))/.6});
   double khi=std::min({maxk,inv(upper[0],1),inv(upper[1],-1),std::tan(std::min(cap,delta+.006))/.6});
   double l0=lower[2],l1=lower[3],u0=upper[2],u1=upper[3];
   if(l0+u1>0)khi=std::min(khi,(u1-l0)/(.27*(l0+u1)));
   if(l1+u0>0)klo=std::max(klo,(l1-u0)/(.27*(l1+u0)));
   khi=std::min(khi,(1-l0/6.)/.27);klo=std::max(klo,(l1/6.-1)/.27);
   if(klo>khi+1e-10)return 1;
   if(klo>khi)klo=khi=(klo+khi)/2;
   double k=clip(braking?pk:wantedk,klo,khi),f0=1-.27*k,f1=1+.27*k;
   double lo=std::max({0.,lower[2]/f0,lower[3]/f1}),hi=std::min({6.,upper[2]/f0,upper[3]/f1});
   if(lo>hi+1e-10)return 2;
   if(lo>hi)lo=hi=(lo+hi)/2;
   double error=v-s[3];integral=braking?0.:clip(integral+error*.01,-.4,.4);
   double common=clip(braking?0.:clip(v/.12+8*error+4*integral,0.,6.),lo,hi);
   double nextu[4]={braking?u[0]:std::atan(.6*k/f0),braking?u[1]:std::atan(.6*k/f1),common*f0,common*f1};
   for(int i=0;i<4;++i)if(!std::isfinite(nextu[i])||nextu[i]<limits[2*i]-1e-10||nextu[i]>limits[2*i+1]+1e-10||std::abs(nextu[i]-u[i])>rate[i]+1e-10)return 3;
   double target=virt(nextu),nr=p[2]*s[7]+p[3]*(target-s[6]),nd=s[6]+.01*nr;
   double nv=p[4]*s[3]+p[5]*(nextu[2]+nextu[3])/2;
   double mv=(s[3]+nv)/2,md=(s[6]+nd)/2;
   double da=p[0]*mv*std::tan(md)/.6*.01+p[1]*(nd-s[6]);
   double nw=p[0]*nv*std::tan(nd)/.6+p[1]*nr;
   double nl=p[6]*nv*std::tan(nd)/.6+p[7]*nr,ml=(s[4]+nl)/2,a=s[2]+da/2;
   s[0]+=.01*(mv*std::cos(a)-ml*std::sin(a));s[1]+=.01*(mv*std::sin(a)+ml*std::cos(a));s[2]+=da;
   s[3]=nv;s[4]=nl;s[5]=nw;s[6]=nd;s[7]=nr;
   std::memcpy(u,nextu,4*sizeof(double));
   std::memcpy(states+(action*steps+j)*8,s,8*sizeof(double));std::memcpy(controls+(action*steps+j)*4,u,4*sizeof(double));
  }
  std::memcpy(memories+action*5,u,4*sizeof(double));memories[action*5+4]=integral;
 }
 return 0;
}
