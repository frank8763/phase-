// Pure-data bounded Hybrid A* and optional obstacle-aware ordering.
// All accepted outputs are independently revalidated by original NumPy.
#include "../v1349_planner_latency_qualification/clearance.cpp"
#include "../v1350_bounded_complete_search/standalone_reeds_shepp.hpp"
#include <array>
#include <chrono>
#include <cstdint>
#include <limits>
#include <memory>
#include <queue>
#include <unordered_map>
#include <vector>

namespace bounded_search {
constexpr double pi=3.14159265358979323846;
using Pose=std::array<double,3>;
struct Field {
  const double* rectangles; int nr; const double* circles; int nc;
  double value(const Pose& p) const {
    double answer;
    footprint_values(p.data(),1,.44,.375,.3,0.,-5.,5.,
                     rectangles,nr,circles,nc,nullptr,0,0.,&answer);
    return answer;
  }
  double point(double x,double y) const {
    double d=std::min({x+5.,5.-x,y+5.,5.-y});
    for (int i=0;i<nr;++i) {
      const double* r=rectangles+4*i;
      double dx=std::abs(x-r[0])-r[2],dy=std::abs(y-r[1])-r[3];
      d=std::min(d,std::max(dx,dy)<=0.?std::max(dx,dy):norm(std::max(dx,0.),std::max(dy,0.)));
    }
    for(int i=0;i<nc;++i)d=std::min(d,norm(x-circles[3*i],y-circles[3*i+1])-circles[3*i+2]);
    return d;
  }
};
struct Key {int x,y,h,g;bool operator==(const Key&o) const{return x==o.x&&y==o.y&&h==o.h&&g==o.g;}};
struct Hash {std::size_t operator()(const Key&k)const {
  std::uint64_t h=1469598103934665603ULL;
  for(int x:{k.x,k.y,k.h,k.g}){h^=std::uint64_t(x+10000);h*=1099511628211ULL;}return h;
}};
double wrap(double x){double v=std::fmod(x+pi,2*pi);if(v<0.)v+=2*pi;return v-pi;}
Key key(const Pose&p,int gear){double a=std::fmod(p[2],2*pi);if(a<0.)a+=2*pi;return {int(std::nearbyint(p[0]/.1)),int(std::nearbyint(p[1]/.1)),int(std::nearbyint(a/(2*pi)*72))%72,gear};}
struct Node {Pose pose;double cost;int parent,steer,gear;};
struct Entry {double f,cost;int id;};
struct Compare {bool operator()(const Entry&a,const Entry&b)const {
  if(a.f!=b.f)return a.f>b.f;if(a.cost!=b.cost)return a.cost>b.cost;return a.id>b.id;
}};
using Piece=std::array<Pose,6>;
Piece primitive(const Pose&pose,int gear,double curvature){
  Piece piece;
  for(int i=0;i<6;++i){
    const double length=gear*((i+1)*.04),yaw=pose[2]+length*curvature;
    if(std::abs(curvature)>1e-9)
      piece[i]={pose[0]+(std::sin(yaw)-std::sin(pose[2]))/curvature,
                pose[1]-(std::cos(yaw)-std::cos(pose[2]))/curvature,yaw};
    else piece[i]={pose[0]+length*std::cos(pose[2]),pose[1]+length*std::sin(pose[2]),yaw};
  }
  return piece;
}

struct AnalyticPiece {std::vector<Pose> poses;std::vector<int> gears;};
bool analytic_connect(const Field&field,const Pose&from,const double*goal,
                      double curvature,double required,AnalyticPiece&output){
  const double radius=1./curvature,c=std::cos(from[2]),s=std::sin(from[2]);
  for(int endpoint=0;endpoint<9;++endpoint)for(int heading=0;heading<36;++heading){
    const double yaw=heading*(2*bounded_search::pi/36);
    // Original goal is a45cm acceptance region, not a requirement to park
    // at an unsafe exact point. Leave13cm for actual final tracking/stop.
    const double angle=(endpoint-1)*(2*bounded_search::pi/8);
    const double gx=goal[0]+(endpoint? .32*std::cos(angle):0.);
    const double gy=goal[1]+(endpoint? .32*std::sin(angle):0.);
    const Pose target{gx-.3*std::cos(yaw),gy-.3*std::sin(yaw),yaw};
    if(field.value(target)<required-1e-8)continue;
    double dx=target[0]-from[0],dy=target[1]-from[1];
    auto solution=::getPath((c*dx+s*dy)/radius,(-s*dx+c*dy)/radius,yaw-from[2]);
    if(!std::isfinite(solution.length())||solution.length()*radius>16.)continue;
    Pose pose=from;AnalyticPiece trial;bool valid=true;
    for(int seg=0;seg<5&&valid;++seg){
      const double length=solution.length_[seg]*radius;
      if(std::abs(length)<1e-10)continue;
      int type=solution.type_[seg],gear=length>0.?1:-1;
      const double k=type==ReedsSheppStateSpace::RS_LEFT?curvature:
          type==ReedsSheppStateSpace::RS_RIGHT?-curvature:0.;
      int count=int(std::ceil(std::abs(length)/.008));
      const double step=length/count;
      for(int tick=0;tick<count;++tick){
        double angle=pose[2]+step*k;
        if(std::abs(k)>1e-10){pose[0]+=(std::sin(angle)-std::sin(pose[2]))/k;pose[1]-=(std::cos(angle)-std::cos(pose[2]))/k;}
        else{pose[0]+=step*std::cos(pose[2]);pose[1]+=step*std::sin(pose[2]);}
        pose[2]=angle;
        if(field.value(pose)<required-1e-8){valid=false;break;}
        trial.poses.push_back(pose);trial.gears.push_back(gear);
      }
    }
    if(valid&&!trial.poses.empty()&&norm(pose[0]-target[0],pose[1]-target[1])<1e-7&&
        std::abs(wrap(pose[2]-yaw))<1e-7){output=std::move(trial);return true;}
  }
  return false;
}

struct Guide {
  static constexpr int side=101;
  std::vector<double> d;std::vector<unsigned char> free;
  explicit Guide(const Field&field,const double*goal,double guard):d(side*side,1e20),free(side*side,0){
    using Q=std::pair<double,int>;std::priority_queue<Q,std::vector<Q>,std::greater<Q>> queue;
    // Orientation-free inscribed-circle guide only. It cannot approve paths
    // or remove exact-footprint search edges, including outside-guide poses.
    for(int y=0;y<side;++y)for(int x=0;x<side;++x){
      double px=-5.+x*.1,py=-5.+y*.1;int id=y*side+x;
      free[id]=field.point(px,py)>=.375+guard;
      if(free[id]&&norm(px-goal[0],py-goal[1])<=.32){d[id]=0.;queue.emplace(0.,id);}
    }
    while(!queue.empty()){
      auto [cost,id]=queue.top();queue.pop();if(cost>d[id]+1e-12)continue;
      int x=id%side,y=id/side;
      for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx){
        if(dx==0&&dy==0)continue;int xx=x+dx,yy=y+dy;
        if(xx<0||xx>=side||yy<0||yy>=side)continue;int next=yy*side+xx;
        if(!free[next])continue;
        if(dx&&dy&&(!free[y*side+xx]||!free[yy*side+x]))continue;
        double trial=cost+(dx&&dy?std::sqrt(.02):.1);
        if(trial<d[next]-1e-12){d[next]=trial;queue.emplace(trial,next);}
      }
    }
  }
  double value(double x,double y)const{
    int xx=int(std::nearbyint((x+5.)/.1)),yy=int(std::nearbyint((y+5.)/.1));
    if(xx<0||xx>=side||yy<0||yy>=side)return 1e20;return d[yy*side+xx];
  }
};
}

extern "C" int plan_route(const double*rectangles,int nr,const double*circles,int nc,
    const double*start,const double*bodygoal,double maxcurvature,double requested_guard,
    int maxexpand,double maxwall,int mode,double*out,int capacity,int*count,double*stats){
  using namespace bounded_search;
  *count=0;const auto begun=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-begun).count();};
  Field field{rectangles,nr,circles,nc};Pose root{start[0],start[1],start[2]};
  double initial=field.value(root);stats[0]=0;stats[1]=0.;stats[2]=initial;
  if(initial<.15-1e-6)return 2;
  double required=std::max(.15,std::min(requested_guard,initial-.001));stats[2]=required;
  const double reargoal[2]={bodygoal[0]-.3,bodygoal[1]};
  std::unique_ptr<Guide> guide;
  if(mode)guide=std::make_unique<Guide>(field,bodygoal,required);
  std::vector<Pose> terminal;
  if(mode==2){
    for(int endpoint=0;endpoint<9;++endpoint)for(int heading=0;heading<36;++heading){
      double yaw=heading*(2*bounded_search::pi/36),angle=(endpoint-1)*(2*bounded_search::pi/8);
      double gx=bodygoal[0]+(endpoint?.32*std::cos(angle):0.),gy=bodygoal[1]+(endpoint?.32*std::sin(angle):0.);
      Pose p{gx-.3*std::cos(yaw),gy-.3*std::sin(yaw),yaw};if(field.value(p)>=required-1e-8)terminal.push_back(p);
    }
  }
  if(terminal.size()>16){
    std::sort(terminal.begin(),terminal.end(),[&](const Pose&a,const Pose&b){
      double ca=field.value(a),cb=field.value(b);if(ca!=cb)return ca>cb;return a<b;
    });terminal.resize(16);
  }
  auto heuristic=[&](const Pose&p){
    if(!mode)return norm(p[0]+.3*std::cos(p[2])-bodygoal[0],p[1]+.3*std::sin(p[2])-bodygoal[1]);
    double cx=p[0]+.3*std::cos(p[2]),cy=p[1]+.3*std::sin(p[2]);
    double eu=norm(cx-bodygoal[0],cy-bodygoal[1]),mapped=guide->value(cx,cy);
    double value=mapped<1e19?std::max(eu,mapped):eu+5.;
    if(mode==2&&!terminal.empty()){
      double cc=std::cos(p[2]),ss=std::sin(p[2]),distance=1e100;
      for(const Pose&target:terminal){
        double dx=target[0]-p[0],dy=target[1]-p[1];
        auto curve=::getPath((cc*dx+ss*dy)*maxcurvature,(-ss*dx+cc*dy)*maxcurvature,target[2]-p[2]);
        distance=std::min(distance,curve.length()/maxcurvature);
      }
      value=std::max(value,distance);
    }
    return value;
  };
  std::array<double,7> steering,curvatures;const double maxsteer=std::atan(.6*maxcurvature);
  for(int i=0;i<7;++i){steering[i]=-maxsteer+i*((2*maxsteer)/6);if(i==6)steering[i]=maxsteer;curvatures[i]=std::tan(steering[i])/.6;}
  std::vector<Node> nodes;nodes.reserve(150000);nodes.push_back({root,0.,-1,-1,1});
  std::unordered_map<Key,double,Hash> best;best.reserve(100000);best[key(root,1)]=0.;
  std::priority_queue<Entry,std::vector<Entry>,Compare>queue;queue.push({heuristic(root),0.,0});
  int expanded=0,goalid=-1,bestid=0;double besth=heuristic(root);AnalyticPiece analytic;
  while(!queue.empty()&&expanded<maxexpand&&elapsed()<maxwall){
    Entry e=queue.top();queue.pop();const Node node=nodes[e.id];
    if(e.cost>best[key(node.pose,node.gear)]+1e-9)continue;++expanded;
    double distance=norm(node.pose[0]+.3*std::cos(node.pose[2])-bodygoal[0],node.pose[1]+.3*std::sin(node.pose[2])-bodygoal[1]);
    if(distance<.32){goalid=e.id;break;}
    if(mode==2 && expanded%128==1 && analytic_connect(field,node.pose,bodygoal,maxcurvature,required,analytic)){
      goalid=e.id;break;
    }
    double hh=heuristic(node.pose);if(hh<besth-.02){besth=hh;bestid=e.id;}
    for(int gear:{1,-1})for(int st=0;st<7;++st){
      Piece piece=primitive(node.pose,gear,curvatures[st]);double minimum=1e100;
      for(const Pose&p:piece)minimum=std::min(minimum,field.value(p));
      if(minimum<required-1e-8)continue;
      Pose endpoint=piece.back();endpoint[2]=wrap(endpoint[2]);Key k=key(endpoint,gear);
      double cost=e.cost+.24*(gear==1?1.:1.8)+(node.gear!=gear?.65:0.);
      cost+=.045*std::abs(steering[st]/maxsteer)+.18*std::max(0.,.30-minimum);
      auto previous=best.find(k);if(previous!=best.end()&&cost>=previous->second-1e-9)continue;
      best[k]=cost;int id=nodes.size();nodes.push_back({endpoint,cost,e.id,st,gear});
      queue.push({cost+1.45*heuristic(endpoint),cost,id});
    }
  }
  stats[0]=expanded;stats[1]=elapsed();stats[3]=goalid>=0;stats[4]=nodes.size();
  int selected=goalid>=0?goalid:bestid;
  if((selected==0&&goalid<0) || (goalid<0&&heuristic(root)-besth<.5))return 1;
  std::vector<int>chain;for(int i=selected;nodes[i].parent>=0;i=nodes[i].parent)chain.push_back(i);
  std::reverse(chain.begin(),chain.end());if(int(chain.size()*6+1+analytic.poses.size())>capacity)return 3;
  std::vector<Pose>path;std::vector<int>gears;path.push_back(root);gears.push_back(1);
  for(int id:chain){const Node&node=nodes[id];Piece piece=primitive(nodes[node.parent].pose,node.gear,curvatures[node.steer]);for(const Pose&p:piece){path.push_back(p);gears.push_back(node.gear);}}
  path.insert(path.end(),analytic.poses.begin(),analytic.poses.end());gears.insert(gears.end(),analytic.gears.begin(),analytic.gears.end());
  double minimum=1e100;
  for(std::size_t i=1;i<path.size();++i){
    Pose a=path[i-1],b=path[i];double da=wrap(b[2]-a[2]);
    for(int j=0;j<5;++j){double t=j/5.;Pose p{a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*da};minimum=std::min(minimum,field.value(p));}
  }
  minimum=std::min(minimum,field.value(path.back()));stats[5]=minimum;stats[1]=elapsed();
  if(minimum<required-1e-8)return 4;
  for(std::size_t i=0;i<path.size();++i){for(int j=0;j<3;++j)out[4*i+j]=path[i][j];out[4*i+3]=gears[i];}
  *count=path.size();stats[6]=heuristic(root)-besth;
  stats[7]=norm(path.back()[0]+.3*std::cos(path.back()[2])-bodygoal[0],path.back()[1]+.3*std::sin(path.back()[2])-bodygoal[1]);
  return 0;
}

// Zero-model connector seam used to test algebra independently from search.
extern "C" int analytic_probe(const double*rectangles,int nr,const double*circles,int nc,
    const double*start,const double*goal,double curvature,double guard,double*out,int capacity,int*count){
  bounded_search::Field field{rectangles,nr,circles,nc};
  bounded_search::Pose from{start[0],start[1],start[2]};bounded_search::AnalyticPiece answer;
  if(!bounded_search::analytic_connect(field,from,goal,curvature,guard,answer)){*count=0;return 1;}
  if(int(answer.poses.size()+1)>capacity){*count=0;return 3;}
  for(int j=0;j<3;++j)out[j]=start[j];out[3]=1.;
  for(std::size_t i=0;i<answer.poses.size();++i){for(int j=0;j<3;++j)out[4*(i+1)+j]=answer.poses[i][j];out[4*(i+1)+3]=answer.gears[i];}
  *count=answer.poses.size()+1;return 0;
}
