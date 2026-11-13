// Analytical source accelerator only. Whole selected source requires Python replay.
#include "../v1046_retreat_entry_timed_route/fast_predict.cpp"
extern "C" int profile(const double *initial,const double *memory,const double *targets,const double *speeds,const int *ticks,const int *modes,int count,const double *limits,const double *rates,const double *p,double *states,double *controls){
 double s[8],mem[5];std::memcpy(s,initial,8*sizeof(double));std::memcpy(mem,memory,5*sizeof(double));int offset=0;
 for(int row=0;row<count;++row){
  if(ticks[row]<1||ticks[row]>12000||offset+ticks[row]>40000)return -1;
  if(!modes[row]){
   double end[5];int code=expand(s,mem,targets+row,speeds+row,1,ticks[row],limits,rates,p,states+offset*8,controls+offset*4,end);if(code)return 100+code;
   std::memcpy(s,states+(offset+ticks[row]-1)*8,8*sizeof(double));std::memcpy(mem,end,5*sizeof(double));
  }else{
   if(speeds[row]!=0.||std::abs(mem[2])>1e-10||std::abs(mem[3])>1e-10||std::abs(targets[row])>.42722137342572125)return 201;
   for(int j=0;j<ticks[row];++j){
    if(std::abs(s[3])>.003||std::abs(s[5])>.16)return 202;
    double lower[4],upper[4];for(int i=0;i<4;++i){lower[i]=std::max(limits[2*i],mem[i]-rates[i]*.01);upper[i]=std::min(limits[2*i+1],mem[i]+rates[i]*.01);}
    if(lower[2]>0||upper[2]<0||lower[3]>0||upper[3]<0)return 203;
    double pk=(inv(mem[0],1)+inv(mem[1],-1))/2,delta=std::atan(.6*pk),cap=.42722137342572125,maxk=std::tan(cap)/.6;
    double lo=std::max({-maxk,inv(lower[0],1),inv(lower[1],-1),std::tan(std::max(-cap,delta-.006))/.6});
    double hi=std::min({maxk,inv(upper[0],1),inv(upper[1],-1),std::tan(std::min(cap,delta+.006))/.6});if(lo>hi+1e-10)return 204;if(lo>hi)lo=hi=(lo+hi)/2;
    double k=clip(std::tan(targets[row])/.6,lo,hi),u[4]={std::atan(.6*k/(1-.27*k)),std::atan(.6*k/(1+.27*k)),0.,0.};
    for(int i=0;i<4;++i)if(u[i]<limits[2*i]-1e-10||u[i]>limits[2*i+1]+1e-10||std::abs(u[i]-mem[i])>rates[i]*.01+1e-10)return 205;
    double nd_rate=p[2]*s[7]+p[3]*(virt(u)-s[6]),nd=s[6]+.01*nd_rate,nv=p[4]*s[3],mv=(s[3]+nv)/2,md=(s[6]+nd)/2;
    double da=p[0]*mv*std::tan(md)/.6*.01+p[1]*(nd-s[6]);double nw=p[0]*nv*std::tan(nd)/.6+p[1]*nd_rate;
    double nl=p[6]*nv*std::tan(nd)/.6+p[7]*nd_rate,ml=(s[4]+nl)/2,angle=s[2]+da/2;
    s[0]+=.01*(mv*std::cos(angle)-ml*std::sin(angle));s[1]+=.01*(mv*std::sin(angle)+ml*std::cos(angle));s[2]+=da;s[3]=nv;s[4]=nl;s[5]=nw;s[6]=nd;s[7]=nd_rate;
    std::memcpy(mem,u,4*sizeof(double));mem[4]=0.;std::memcpy(states+(offset+j)*8,s,8*sizeof(double));std::memcpy(controls+(offset+j)*4,u,4*sizeof(double));
   }
  }
  offset+=ticks[row];
 }
 return offset;
}
