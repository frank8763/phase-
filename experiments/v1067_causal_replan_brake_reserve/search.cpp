// Analytical proposal only. Every returned complete input is independently
// reconstructed by the original Python predictor before it can be admitted.
#include "../v1046_retreat_entry_timed_route/fast_predict.cpp"
#include <vector>
#include <array>
#include <queue>
#include <unordered_map>
#include <chrono>
#include <cstdint>
#include <limits>

struct Node {
 std::array<double,8> s;
 std::array<double,5> m;
 int parent, action, ticks, elapsed, gear;
 double g;
};
struct Entry {double f,g;int id;bool operator<(const Entry&o)const{return f>o.f;}};
struct Key {std::array<int,9> a;bool operator==(const Key&o)const{return a==o.a;}};
struct Hash {size_t operator()(const Key&k)const{size_t h=1469598103934665603ULL;for(int x:k.a){h^=size_t(x+100000);h*=1099511628211ULL;}return h;}};
static constexpr double pi=3.14159265358979323846, period=2*pi/.32, required=.24353421020226934, rho=.5782084401781719;
using Point=std::array<double,2>;using Polygon=std::vector<Point>;
static Polygon polygon(const double *b){
 Polygon p={Point{-b[8],-b[12]},Point{b[0],-b[12]},Point{b[0],b[4]},Point{-b[8],b[4]}};
 for(int k=0;k<16;k++){double nx=std::cos(k*pi/8),ny=std::sin(k*pi/8);Polygon out;for(size_t i=0;i<p.size();i++){auto a=p[i],z=p[(i+1)%p.size()];double da=a[0]*nx+a[1]*ny-b[k],dz=z[0]*nx+z[1]*ny-b[k];if(da<=0)out.push_back(a);if((da<0&&dz>0)||(dz<0&&da>0)){double t=da/(da-dz);out.push_back({a[0]+t*(z[0]-a[0]),a[1]+t*(z[1]-a[1])});}}p=std::move(out);if(p.empty())return p;}
 return p;
}
static double polygon_distance(double x,double y,double a,const Polygon&p){
 if(p.empty())return -1e100;double c=std::cos(a),s=std::sin(a),d=1e100;Point corners[4];int z=0;bool separated=false;double minx=1e100,maxx=-1e100,miny=1e100,maxy=-1e100;
 for(int u:{-1,1})for(int v:{-1,1})corners[z++]={x+c*u*.44-s*v*.375,y+s*u*.44+c*v*.375};
 for(const auto&q:p){double dx=q[0]-x,dy=q[1]-y,lx=dx*c+dy*s,ly=-dx*s+dy*c;minx=std::min(minx,lx);maxx=std::max(maxx,lx);miny=std::min(miny,ly);maxy=std::max(maxy,ly);d=std::min(d,std::hypot(std::max(0.,std::abs(lx)-.44),std::max(0.,std::abs(ly)-.375)));}
 separated=minx>.44||maxx<-.44||miny>.375||maxy<-.375;
 for(size_t i=0;i<p.size();i++){
  Point q=p[i],r=p[(i+1)%p.size()];double ex=r[0]-q[0],ey=r[1]-q[1],n2=ex*ex+ey*ey;if(n2<1e-24)continue;double pmin=1e100,pmax=-1e100,bmin=1e100,bmax=-1e100;
  for(auto&v:p){double value=-ey*v[0]+ex*v[1];pmin=std::min(pmin,value);pmax=std::max(pmax,value);}for(auto&v:corners){double value=-ey*v[0]+ex*v[1];bmin=std::min(bmin,value);bmax=std::max(bmax,value);double dx=v[0]-q[0],dy=v[1]-q[1],t=clip((dx*ex+dy*ey)/n2,0.,1.);d=std::min(d,std::hypot(dx-t*ex,dy-t*ey));}separated=separated||bmin>pmax||bmax<pmin;
 }
 return separated?d:0.;
}
static Key key(const Node&n){
 double a=std::fmod(n.s[2]+20*pi,2*pi);
 return {{{int(std::round(n.s[0]/.02)),int(std::round(n.s[1]/.025)),int(std::round(a*288/(2*pi)))%288,int(std::round(n.s[6]/.1068053433564303)),int(std::round(n.s[7]/.06)),int(std::round(n.s[3]/.02)),int(std::round(n.m[4]/.04)),int(std::round(std::fmod(n.elapsed*.01,period)/.5)),n.gear}}};
}
struct Geometry {
 const double *rect,*circle,*support;int nr,nc,nb;double start,bin;
 const std::vector<Polygon>*polys=nullptr;
 double static_value(double x,double y,double a)const{
  double c=std::cos(a),s=std::sin(a),ac=std::abs(c),as=std::abs(s),ex=.44*ac+.375*as,ey=.44*as+.375*ac;
  double low=std::min({x-ex+5,5-x-ex,y-ey+5,5-y-ey});
  for(int j=0;j<nc;j++){
   double dx=circle[3*j]-x,dy=circle[3*j+1]-y;
   double u=std::abs(dx*c+dy*s)-.44,v=std::abs(-dx*s+dy*c)-.375;
   double d=std::max(u,v)<=0?std::max(u,v):std::hypot(std::max(0.,u),std::max(0.,v));
   low=std::min(low,d-circle[3*j+2]);
  }
  static const int signs[4][2]={{-1,-1},{-1,1},{1,1},{1,-1}};
  for(int j=0;j<nr;j++){
   const double *r=rect+4*j;double dx=r[0]-x,dy=r[1]-y;
   double sep=std::max({std::abs(dx)-r[2]-ex,std::abs(dy)-r[3]-ey,std::abs(dx*c+dy*s)-.44-r[2]*ac-r[3]*as,std::abs(-dx*s+dy*c)-.375-r[2]*as-r[3]*ac});
   if(sep<=0){low=std::min(low,sep);continue;}
   if(sep>=low)continue;
   double d=1e100;
   for(auto &q:signs){
    double bx=x+c*q[0]*.44-s*q[1]*.375,by=y+s*q[0]*.44+c*q[1]*.375;
    d=std::min(d,std::hypot(std::max(0.,std::abs(bx-r[0])-r[2]),std::max(0.,std::abs(by-r[1])-r[3])));
    double ux=r[0]+q[0]*r[2]-x,uy=r[1]+q[1]*r[3]-y;
    d=std::min(d,std::hypot(std::max(0.,std::abs(ux*c+uy*s)-.44),std::max(0.,std::abs(-ux*s+uy*c)-.375)));
   }
   low=std::min(low,d);
  }
  return low;
 }
 double value(const double *s,int tick,bool full=false)const{
  double low=static_value(s[0],s[1],s[2]);if(!support)return low;
  double phase=std::fmod(start+tick*.01,period);if(phase<0)phase+=period;
  int row=std::min(nb-1,int(phase/bin));double c=std::cos(s[2]),sn=std::sin(s[2]),d=-1e100;
  for(int k=0;k<16;k++){
   double nx=std::cos(k*pi/8),ny=std::sin(k*pi/8),b=full?support[nb*16+k]:support[row*16+k];
   d=std::max(d,s[0]*nx+s[1]*ny-.44*std::abs(c*nx+sn*ny)-.375*std::abs(-sn*nx+c*ny)-b-.1);
  }
  if(polys&&d<required)d=polygon_distance(s[0],s[1],s[2],(*polys)[full?nb:row])-.1;
  return std::min(low,d);
 }
};
extern "C" double static_pose(double x,double y,double a,const double*r,int nr,const double*c,int nc){return Geometry{r,c,nullptr,nr,nc,0,0,0}.static_value(x,y,a);}
extern "C" double stop_lower(const double *initial,const double *memory,const double *limits,const double *rates,const double *parameters,const double *rect,int nr,const double *circles,int nc,int stop_ticks){
 Geometry geom{rect,circles,nullptr,nr,nc,0,0,0};double state[8],mem[5],ss[334*8],uu[334*4],mm[5],zero=0.;std::copy(initial,initial+8,state);std::copy(memory,memory+5,mem);double low=geom.static_value(state[0],state[1],state[2]);
 for(int done=0;done<stop_ticks;){int n=std::min(334,stop_ticks-done);int code=expand(state,mem,&zero,&zero,1,n,limits,rates,parameters,ss,uu,mm);if(code)return -1e100;for(int t=0;t<n;t++){double *s=ss+t*8;if(std::abs(s[3])>.13||std::abs(s[4])>.03||std::abs(s[5])>.16)return -1e100;low=std::min(low,geom.static_value(s[0],s[1],s[2]));}std::copy(ss+(n-1)*8,ss+n*8,state);std::copy(mm,mm+5,mem);done+=n;}
 return low;
}
extern "C" int straight_best(double x,double top,double bottom,double speed,const double *support,int nb,double bin,const double *rect,int nr,const double *circles,int nc,double *result){
 Geometry geom{rect,circles,support,nr,nc,nb,0,bin};std::vector<Polygon> polys;for(int j=0;j<nb;j++)polys.push_back(polygon(support+j*16));geom.polys=&polys;int n=int(std::ceil((top-bottom)/(speed*.01)))+1;std::vector<double> body(n*16);double staticlow=1e100;
 for(int k=0;k<n;k++){double y=top-speed*k*.01;staticlow=std::min(staticlow,geom.static_value(x,y,-pi/2));for(int j=0;j<16;j++){double nx=std::cos(j*pi/8),ny=std::sin(j*pi/8);body[k*16+j]=x*nx+y*ny-.44*std::abs(ny)-.375*std::abs(nx)-.1;}}
 double best=-1e100;int phase=-1,worst=-1;
 for(int j=0;j<nb;j++){double lower=staticlow;int at=0;for(int k=0;k<n;k++){double t=std::fmod(j*bin+k*.01,period);int row=std::min(nb-1,int(t/bin));double d=-1e100;for(int z=0;z<16;z++)d=std::max(d,body[k*16+z]-support[row*16+z]);if(d<required)d=polygon_distance(x,top-speed*k*.01,-pi/2,polys[row])-.1;if(d<lower){lower=d;at=k;}if(lower<best)break;}if(lower>best){best=lower;phase=j;worst=at;}}
 result[0]=best;result[1]=phase*bin;result[2]=staticlow;result[3]=top-speed*worst*.01;return 0;
}
extern "C" int search(const double *initial,const double *memory,const double *limits,const double *rates,const double *parameters,const double *rect,int nr,const double *circles,int nc,const double *support,int nb,double bin,double start,const double *goal,double maxwall,int maxexpand,double *actions,int *na,double *stats){
 auto begun=std::chrono::steady_clock::now();Geometry geom{rect,circles,nb?support:nullptr,nr,nc,nb,start,bin};std::vector<Polygon> polys;for(int j=0;j<=nb&&nb;j++)polys.push_back(polygon(support+j*16));if(nb)geom.polys=&polys;
 auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-begun).count();};
 std::vector<Node> nodes;nodes.reserve(500000);Node root;std::copy(initial,initial+8,root.s.begin());std::copy(memory,memory+5,root.m.begin());root.parent=-1;root.action=-1;root.ticks=root.elapsed=root.gear=0;root.g=0;nodes.push_back(root);
 if(geom.value(root.s.data(),0)<required){stats[0]=0;stats[1]=elapsed();return 2;}
 // Optimistic center-map distance supplies the global topology (including
 // the central opening). It NEVER admits a body/control edge.
 const int side=200;const double cell=.05;std::vector<double> guide(side*side,1e100);std::vector<unsigned char> free(side*side);std::priority_queue<Entry> grid;
 for(int y=0;y<side;y++)for(int x=0;x<side;x++){
  double px=-5+(x+.5)*cell,py=-5+(y+.5)*cell,low=std::min(5-std::abs(px),5-std::abs(py));
  for(int j=0;j<nr;j++){auto r=rect+4*j;double dx=std::abs(px-r[0])-r[2],dy=std::abs(py-r[1])-r[3];low=std::min(low,std::max(dx,dy)<=0?std::max(dx,dy):std::hypot(std::max(0.,dx),std::max(0.,dy)));}
  for(int j=0;j<nc;j++)low=std::min(low,std::hypot(px-circles[3*j],py-circles[3*j+1])-circles[3*j+2]);
  int id=y*side+x;free[id]=low>=.375+required;if(free[id]&&std::hypot(px-goal[0],py-goal[1])<=.2){guide[id]=0.;grid.push({0,0,id});}
 }
 while(!grid.empty()){auto e=grid.top();grid.pop();if(e.g>guide[e.id]+1e-12)continue;int x=e.id%side,y=e.id/side;for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){if(!dx&&!dy)continue;int xx=x+dx,yy=y+dy;if(xx<0||xx>=side||yy<0||yy>=side)continue;int id=yy*side+xx;if(!free[id])continue;double cost=e.g+cell*std::hypot(dx,dy);if(cost<guide[id]){guide[id]=cost;grid.push({cost,cost,id});}}}
 auto heuristic=[&](const Node&n){double dx=goal[0]-n.s[0],dy=goal[1]-n.s[1],a=std::atan2(dy,dx)-n.s[2],direct=std::max(0.,std::hypot(dx,dy)-.2);int xx=int((n.s[0]+5)/cell),yy=int((n.s[1]+5)/cell);double h=xx>=0&&xx<side&&yy>=0&&yy<side&&guide[yy*side+xx]<1e90?std::max(direct,guide[yy*side+xx]):direct+2.;return h+.12*std::abs(std::atan2(std::sin(a),std::cos(a)));};
 std::priority_queue<Entry> heap;heap.push({2.5*heuristic(root),0,0});std::unordered_map<Key,double,Hash> best;best[key(root)]=0;
 double targets[5]={-.42722137342572125,-.21361068671286063,0,.21361068671286063,.42722137342572125};
 int expanded=0,chosen=-1,partial=-1,rejected=0;double closest=std::hypot(root.s[0]-goal[0],root.s[1]-goal[1]),root_h=heuristic(root),partial_score=-1e100;
 std::vector<double> ss(5*200*8),uu(5*200*4),mm(5*5);
 while(!heap.empty()&&expanded<maxexpand&&elapsed()<maxwall){
  auto item=heap.top();heap.pop();const Node node=nodes[item.id];auto found=best.find(key(node));if(found!=best.end()&&item.g>found->second+1e-10)continue;
  expanded++;double distance=std::hypot(node.s[0]-goal[0],node.s[1]-goal[1]);closest=std::min(closest,distance);
  double improvement=root_h-heuristic(node),score=improvement-.02*node.g;
  if(node.elapsed>=400&&improvement>=.15&&score>partial_score+.01){
   double zero=0.;int code=expand(node.s.data(),node.m.data(),&zero,&zero,1,200,limits,rates,parameters,ss.data(),uu.data(),mm.data());bool valid=code==0;
   for(int t=0;valid&&t<200;t++)valid=geom.value(ss.data()+t*8,node.elapsed+t+1)>=required;
   if(valid&&geom.value(ss.data()+199*8,node.elapsed+200,true)>=required+.02){partial=item.id;partial_score=score;}
  }
  if(node.elapsed&&distance+.08<=.45&&node.gear>=0){
   double zero=0.;int code=expand(node.s.data(),node.m.data(),&zero,&zero,1,200,limits,rates,parameters,ss.data(),uu.data(),mm.data());bool valid=code==0;
   for(int t=0;valid&&t<200;t++)valid=geom.value(ss.data()+t*8,node.elapsed+t+1)>=required;
   if(valid&&geom.value(ss.data()+199*8,node.elapsed+200,true)>=required&&std::hypot(ss[199*8]-goal[0],ss[199*8+1]-goal[1])+.08<=.45){chosen=item.id;break;}
  }
  if(node.elapsed>39500||nodes.size()>1800000)continue;
  bool stopped=std::abs(node.s[3])<=.003&&std::abs(node.m[2])+std::abs(node.m[3])<=1e-10;
  for(int direction:{1,-1,0}){
   if(direction<0&&!stopped&&node.gear>=0)continue;if(direction>0&&!stopped&&node.gear<0)continue;
   int nt=direction?5:1,steps=direction?125:200;double speeds[5];std::fill(speeds,speeds+5,direction>0?.08:direction<0?-.03:0.);double zero=0.;double *ts=direction?targets:&zero;
   int code=expand(node.s.data(),node.m.data(),ts,speeds,nt,steps,limits,rates,parameters,ss.data(),uu.data(),mm.data());if(code)continue;
   for(int j=0;j<nt;j++){
    double *path=ss.data()+j*steps*8;bool valid=true;
    // Native geometry avoids sparse rejection at the narrow declared start.
    for(int t=0;t<steps;t++){
     double *q=path+t*8;
     if(std::abs(q[3])>.13||std::abs(q[4])>.03||std::abs(q[5])>.16||geom.value(q,node.elapsed+t+1)<required){valid=false;break;}
    }
    if(!valid){rejected++;continue;}
    Node child;std::copy(path+(steps-1)*8,path+steps*8,child.s.begin());std::copy(mm.data()+j*5,mm.data()+(j+1)*5,child.m.begin());child.parent=item.id;child.action=direction?j+5*(direction<0):10;child.ticks=steps;child.elapsed=node.elapsed+steps;child.gear=direction?direction:node.gear;
    child.g=node.g+steps*.01*(direction>0?.08:direction<0?.07:.008)*(1+(!direction?0:.12*std::abs(ts[j])/.42722137342572125))+(direction&&node.gear&&direction!=node.gear?.25:0);
    Key marker=key(child);auto old=best.find(marker);if(old!=best.end()&&child.g>=old->second-1e-10)continue;best[marker]=child.g;int id=nodes.size();nodes.push_back(child);heap.push({child.g+2.5*heuristic(child),child.g,id});
   }
  }
 }
 stats[0]=expanded;stats[1]=elapsed();stats[2]=closest;stats[3]=nodes.size();stats[4]=rejected;*na=0;
 bool finite_prefix=chosen<0;
 // A wall-clock cap is an exception, never a different successful policy.
 // Finite proposals must come from the same fixed expansion budget/open set.
 if(finite_prefix&&elapsed()>=maxwall&&expanded<maxexpand&&!heap.empty())return 5;
 if(finite_prefix)chosen=partial;if(chosen<0)return 1;
 std::vector<Node> chain;for(int i=chosen;nodes[i].parent!=-1;i=nodes[i].parent)chain.push_back(nodes[i]);std::reverse(chain.begin(),chain.end());if(chain.size()>1000)return 3;
 for(auto&n:chain){actions[3*(*na)]=n.action;actions[3*(*na)+1]=n.ticks;actions[3*(*na)+2]=n.elapsed;(*na)++;}
 return finite_prefix?4:0;
}
