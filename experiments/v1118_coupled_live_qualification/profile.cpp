// Analytical accelerator only; selected source must be fully replayed in Python.
#include "../v1046_retreat_entry_timed_route/fast_predict.cpp"
static int completed_work=0;
extern "C" int profile_work(){return completed_work;}
static void advance(double *s,const double *u,const double *p,bool coupled,double request){
 double nr=p[2]*s[7]+p[3]*(virt(u)-s[6]),nd=s[6]+.01*nr;
 double nv=p[4]*s[3]+p[5]*(u[2]+u[3])/2;
 if(std::abs(request-.08)<=1e-12)nv+=p[8]*(u[2]+u[3])/2*std::pow(std::tan(nd)/.6,2);
 if(coupled)nv+=p[9]*std::sin((s[6]+nd)/2)*nr;
 double mv=(s[3]+nv)/2,md=(s[6]+nd)/2,da=p[0]*mv*std::tan(md)/.6*.01+p[1]*(nd-s[6]);
 double nw=p[0]*nv*std::tan(nd)/.6+p[1]*nr,nl=p[6]*nv*std::tan(nd)/.6+p[7]*nr,ml=(s[4]+nl)/2,a=s[2]+da/2;
 s[0]+=.01*(mv*std::cos(a)-ml*std::sin(a));s[1]+=.01*(mv*std::sin(a)+ml*std::cos(a));s[2]+=da;s[3]=nv;s[4]=nl;s[5]=nw;s[6]=nd;s[7]=nr;
}
extern "C" int profile(const double *initial,const double *memory,const double *targets,const double *speeds,const int *ticks,const int *modes,int count,const double *limits,const double *rates,const double *p,double *states,double *controls){
 completed_work=0;double s[8],mem[5];std::memcpy(s,initial,8*sizeof(double));std::memcpy(mem,memory,5*sizeof(double));int offset=0;bool coupled=p[10]!=0.,active=p[11]!=0.;if(active&&!coupled)return -207;
 for(int row=0;row<count;++row){
  if(ticks[row]<1||ticks[row]>12000||offset+ticks[row]>40000)return -1;
  if(!modes[row])active=false;
  if(std::abs(speeds[row])>=.005)coupled=false;
  for(int j=0;j<ticks[row];++j){
   double u[4];
   if(!modes[row]){
    double temp[8],end[5];int code=expand(s,mem,targets+row,speeds+row,1,1,limits,rates,p,temp,u,end);if(code)return -100-code;
    if(coupled){if(std::max(std::abs(u[2]),std::abs(u[3]))>1e-10)return -206;advance(s,u,p,true,speeds[row]);}
    else std::memcpy(s,temp,8*sizeof(double));
    std::memcpy(mem,end,5*sizeof(double));
   }else{
    if(speeds[row]!=0.||std::abs(mem[2])>1e-10||std::abs(mem[3])>1e-10||std::abs(targets[row])>.42722137342572125)return -201;
    if((!active&&(std::abs(s[3])>.003||std::abs(s[5])>.003))||(active&&(std::abs(s[3])>.01||std::abs(s[5])>.16)))return -202;
    double lower[4],upper[4];for(int i=0;i<4;++i){lower[i]=std::max(limits[2*i],mem[i]-rates[i]*.01);upper[i]=std::min(limits[2*i+1],mem[i]+rates[i]*.01);}
    if(lower[2]>0||upper[2]<0||lower[3]>0||upper[3]<0)return -203;
    double pk=(inv(mem[0],1)+inv(mem[1],-1))/2,delta=std::atan(.6*pk),cap=.42722137342572125,maxk=std::tan(cap)/.6;
    double lo=std::max({-maxk,inv(lower[0],1),inv(lower[1],-1),std::tan(std::max(-cap,delta-.002))/.6});
    double hi=std::min({maxk,inv(upper[0],1),inv(upper[1],-1),std::tan(std::min(cap,delta+.002))/.6});if(lo>hi+1e-10)return -204;if(lo>hi)lo=hi=(lo+hi)/2;
    double k=clip(std::tan(targets[row])/.6,lo,hi);u[0]=std::atan(.6*k/(1-.27*k));u[1]=std::atan(.6*k/(1+.27*k));u[2]=u[3]=0.;
    for(int i=0;i<4;++i)if(u[i]<limits[2*i]-1e-10||u[i]>limits[2*i+1]+1e-10||std::abs(u[i]-mem[i])>rates[i]*.01+1e-10)return -205;
    coupled=active=true;advance(s,u,p,true,0.);std::memcpy(mem,u,4*sizeof(double));mem[4]=0.;
   }
   std::memcpy(states+(offset+j)*8,s,8*sizeof(double));std::memcpy(controls+(offset+j)*4,u,4*sizeof(double));
   ++completed_work;
  }
  offset+=ticks[row];
 }
 return offset;
}
