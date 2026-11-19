// Engineering joint space-time/velocity lattice. Nominal geometry only.
// Original geometry, primitive curvature and guide implementation unchanged.
#include "../v1358_terminal_contract/search.cpp"

namespace timed_vehicle {
using bounded_search::Pose;
struct Key {
  int x,y,h,g,v,t;
  bool operator==(const Key&o)const{return x==o.x&&y==o.y&&h==o.h&&g==o.g&&v==o.v&&t==o.t;}
};
struct Hash {std::size_t operator()(const Key&k)const{
  std::uint64_t h=1469598103934665603ULL;
  for(int x:{k.x,k.y,k.h,k.g,k.v,k.t}){h^=std::uint64_t(x+10000);h*=1099511628211ULL;}return h;
}};
Key key(const Pose&p,int gear,int velocity,double time){
  const auto a=bounded_search::key(p,gear);
  return {a.x,a.y,a.h,gear,velocity,int(std::nearbyint(time/.2))};
}
struct Sample {Pose pose;double time,speed;int gear,action;};
struct Node {Pose pose;double time,cost;int parent,steer,gear,velocity,action;};
struct Entry {double f,cost;int id;};
struct Compare {bool operator()(const Entry&a,const Entry&b)const{
  if(a.f!=b.f)return a.f>b.f;if(a.cost!=b.cost)return a.cost>b.cost;return a.id>b.id;
}};
struct Dynamic {
  const double*balls;int count;double dt;
  double value(const Pose&p,double time)const{
    const int i=std::max(0,int(std::floor((time+1e-8)/dt)));
    if(i>=count)return -1e100;
    const double*b=balls+3*i,c=std::cos(p[2]),s=std::sin(p[2]);
    const double dx=b[0]-(p[0]+.3*c),dy=b[1]-(p[1]+.3*s);
    const double a=std::abs(c*dx+s*dy)-.44,z=std::abs(-s*dx+c*dy)-.375;
    return (std::max(a,z)<=0?std::max(a,z):std::hypot(std::max(a,0.),std::max(z,0.)))-b[2];
  }
};
Pose advance(const Pose&p,double distance,double curvature){
  const double yaw=p[2]+distance*curvature;
  if(std::abs(curvature)<1e-10)return {p[0]+distance*std::cos(p[2]),p[1]+distance*std::sin(p[2]),yaw};
  return {p[0]+(std::sin(yaw)-std::sin(p[2]))/curvature,p[1]-(std::cos(yaw)-std::cos(p[2]))/curvature,yaw};
}
// action1acceleration,2cruise,3brake-to-rest,4wait. A rest node permits
// holding, never an instantaneous stop from a cruising state.
std::vector<Sample> primitive(const Node&n,int action,int gear,double curvature){
  std::vector<Sample> out;double offset=0.;
  auto hold=[&](double duration){
    const int count=int(std::round(duration/.1));
    for(int j=1;j<=count;++j)out.push_back({n.pose,n.time+offset+j*.1,0.,n.gear,action});
    offset+=duration;
  };
  if(action==4){hold(.4);return out;}
  if(action==1){
    if(n.gear&&n.gear!=gear)hold(2.0);
    hold(.4);
  }
  const double duration=action==1?1.0:action==2?2.4:2.0;
  const int count=int(std::round(duration/.1));
  for(int j=1;j<=count;++j){
    const double t=j*.1;
    const double distance=action==1?.05*t*t:action==2?.1*t:.1*t-.025*t*t;
    const double speed=action==1?.1*t:action==2?.1:.1-.05*t;
    out.push_back({advance(n.pose,gear*distance,curvature),n.time+offset+t,gear*speed,gear,action});
  }
  if(action==3){
    const Pose end=out.back().pose;
    for(int j=1;j<=4;++j)out.push_back({end,n.time+offset+duration+j*.1,0.,gear,action});
  }
  return out;
}
}

extern "C" int plan_timed(const double*rectangles,int nr,const double*circles,int nc,
    const double*start,const double*goal,const double*balls,int nb,double dt,
    int maxexpand,double maxwall,double*out,int capacity,int*count,double*stats){
  using namespace timed_vehicle;
  *count=0;const auto begun=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-begun).count();};
  bounded_search::Field field{rectangles,nr,circles,nc};Dynamic dynamic{balls,nb,dt};
  const Pose root{start[0],start[1],start[2]};
  const double initial=std::min(field.value(root),dynamic.value(root,0.));
  stats[0]=0;stats[1]=0;stats[2]=initial;
  if(initial<.22-1e-8)return 2;
  const double required=std::max(.22,std::min(.27,initial-.001));stats[2]=required;
  bounded_search::Guide guide(field,goal,required);
  auto heuristic=[&](const Pose&p){
    const double x=p[0]+.3*std::cos(p[2]),y=p[1]+.3*std::sin(p[2]);
    const double eu=std::hypot(x-goal[0],y-goal[1]),mapped=guide.value(x,y);
    return (mapped<1e19?std::max(eu,mapped):eu+5.)/.1;
  };
  const double maxsteer=std::atan(.6*.5);std::array<double,7> curvatures;
  for(int j=0;j<7;++j)curvatures[j]=std::tan(-maxsteer+j*(2*maxsteer/6))/.6;
  std::vector<Node> nodes;nodes.reserve(180000);nodes.push_back({root,0.,0.,-1,3,0,0,0});
  std::unordered_map<Key,double,Hash> best;best.reserve(200000);best[key(root,0,0,0.)]=0.;
  std::priority_queue<Entry,std::vector<Entry>,Compare> queue;queue.push({heuristic(root),0.,0});
  int expanded=0,goalid=-1;double closest=1e100;
  while(!queue.empty()&&expanded<maxexpand&&elapsed()<maxwall){
    const auto e=queue.top();queue.pop();const Node node=nodes[e.id];
    if(e.cost>best[key(node.pose,node.gear,node.velocity,node.time)]+1e-9)continue;
    ++expanded;
    const double distance=std::hypot(node.pose[0]+.3*std::cos(node.pose[2])-goal[0],node.pose[1]+.3*std::sin(node.pose[2])-goal[1]);
    closest=std::min(closest,distance);
    if(distance<=.32&&node.velocity==0){
      bool terminal=true;
      for(double t=node.time;t<=node.time+2.+1e-8;t+=.1)
        terminal &= std::min(field.value(node.pose),dynamic.value(node.pose,t))>=required-1e-8;
      if(terminal){goalid=e.id;break;}
    }
    auto insert=[&](int action,int gear,int st){
      const auto samples=primitive(node,action,gear,curvatures[st]);
      if(samples.empty()||samples.back().time>80.-2.0001)return;
      for(const auto&s:samples)
        if(std::min(field.value(s.pose),dynamic.value(s.pose,s.time))<required-1e-8)return;
      const auto&last=samples.back();Pose pose=last.pose;pose[2]=bounded_search::wrap(pose[2]);
      const int velocity=action==1||action==2?1:0;
      const int newgear=action==4?node.gear:gear;
      const auto k=key(pose,newgear,velocity,last.time);
      const double cost=node.cost+last.time-node.time+(gear<0?.08:0.)+(action==3?.05:0.);
      const auto old=best.find(k);if(old!=best.end()&&cost>=old->second-1e-9)return;
      best[k]=cost;const int id=int(nodes.size());nodes.push_back({pose,last.time,cost,e.id,st,newgear,velocity,action});
      queue.push({cost+1.45*heuristic(pose),cost,id});
    };
    if(node.velocity==0){
      insert(4,node.gear,node.steer);
      for(int gear:{1,-1})for(int st=0;st<7;++st)insert(1,gear,st);
    }else{
      insert(3,node.gear,node.steer);
      for(int st=0;st<7;++st)insert(2,node.gear,st);
    }
  }
  stats[0]=expanded;stats[1]=elapsed();stats[3]=goalid>=0;stats[4]=nodes.size();stats[5]=closest;
  if(goalid<0)return 1;
  std::vector<int>chain;for(int id=goalid;nodes[id].parent>=0;id=nodes[id].parent)chain.push_back(id);
  std::reverse(chain.begin(),chain.end());std::vector<Sample> path;path.push_back({root,0.,0.,0,0});
  for(int id:chain){
    const auto&n=nodes[id];auto points=primitive(nodes[n.parent],n.action,n.gear,curvatures[n.steer]);
    path.insert(path.end(),points.begin(),points.end());
  }
  const auto last=path.back();
  for(int j=1;j<=20;++j)path.push_back({last.pose,last.time+j*.1,0.,last.gear,5});
  if(int(path.size())>capacity)return 3;
  for(std::size_t i=0;i<path.size();++i){
    for(int j=0;j<3;++j)out[i*7+j]=path[i].pose[j];
    out[i*7+3]=path[i].time;out[i*7+4]=path[i].speed;out[i*7+5]=path[i].gear;out[i*7+6]=path[i].action;
  }
  *count=int(path.size());stats[6]=last.time;stats[7]=path.size();return 0;
}
