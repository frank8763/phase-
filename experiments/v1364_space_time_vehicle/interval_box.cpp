// Safe arrival-interval propagation over the same nominal vehicle primitives.
// Rest labels can wait inside one safe interval; cruising labels cannot.
#include "search.cpp"
#include <bitset>

namespace interval_box_vehicle {
using bounded_search::Pose;
struct Key {int x,y,h,g,v,s;bool operator==(const Key&o)const{
  return x==o.x&&y==o.y&&h==o.h&&g==o.g&&v==o.v&&s==o.s;
}};
struct Hash {std::size_t operator()(const Key&k)const{
  std::uint64_t h=1469598103934665603ULL;
  for(int x:{k.x,k.y,k.h,k.g,k.v,k.s}){h^=std::uint64_t(x+10000);h*=1099511628211ULL;}return h;
}};
Key key(const Pose&p,int gear,int velocity,int steer){const auto k=bounded_search::key(p,gear);return {k.x,k.y,k.h,gear,velocity,steer};}
struct Node {Pose pose;int lo,hi,gear,velocity,steer,parent,action,duration;};
struct Sample {Pose pose;double offset,speed;int gear,action;};
struct Cached {double x,y,c,s,offset,speed;int gear,action;Pose pose;};
using Coverage=std::bitset<401>;
struct World {
  bounded_search::Field field;const double*balls;int nb;double required;
  double value(double x,double y,double c,double s,int index)const{
    if(index<0||index>=nb)return -1e100;
    const double*b=balls+index*4,dx=b[0]-x,dy=b[1]-y;
    const double rx=b[2],ry=b[3],ac=std::abs(c),as=std::abs(s);
    const double ex=ac*.44+as*.375,ey=as*.44+ac*.375;
    const double separation=std::max({std::abs(dx)-rx-ex,std::abs(dy)-ry-ey,
      std::abs(dx*c+dy*s)-.44-rx*ac-ry*as,
      std::abs(-dx*s+dy*c)-.375-rx*as-ry*ac});
    // Separating-axis distance is a conservative lower bound. Far clear
    // states need no corner square-roots; near states use the original exact
    // rectangle-distance equations, then add the unchanged actor radius.10.
    if(separation<=0.||separation>=required+.10)return separation-.10;
    double distance=1e100;
    for(int sx:{-1,1})for(int sy:{-1,1}){
      const double qx=c*(sx*.44)-s*(sy*.375),qy=s*(sx*.44)+c*(sy*.375);
      distance=std::min(distance,std::hypot(std::max(std::abs(qx-dx)-rx,0.),std::max(std::abs(qy-dy)-ry,0.)));
      const double vx=dx+sx*rx,vy=dy+sy*ry;
      distance=std::min(distance,std::hypot(std::max(std::abs(vx*c+vy*s)-.44,0.),std::max(std::abs(-vx*s+vy*c)-.375,0.)));
    }
    return distance-.10;
  }
  bool safe(const Pose&p,int tick)const{
    const double c=std::cos(p[2]),s=std::sin(p[2]);
    return value(p[0]+.3*c,p[1]+.3*s,c,s,tick)>=required-1e-8;
  }
};
std::vector<Cached> motion(const Node&n,int action,int gear,int steer,const std::array<double,7>&curvatures){
  timed_vehicle::Node origin{n.pose,0.,0.,-1,n.steer,n.gear,n.velocity,0};
  const auto path=timed_vehicle::primitive(origin,action,gear,curvatures[steer]);std::vector<Cached> out;
  for(const auto&s:path){const double c=std::cos(s.pose[2]),z=std::sin(s.pose[2]);
    out.push_back({s.pose[0]+.3*c,s.pose[1]+.3*z,c,z,s.time,s.speed,s.gear,s.action,s.pose});}
  return out;
}
}

extern "C" int plan_interval_box(const double*rectangles,int nr,const double*circles,int nc,
    const double*start,const double*goal,const double*balls,int nb,double dt,
    int maxexpand,double maxwall,double*out,int capacity,int*count,double*stats){
  using namespace interval_box_vehicle;
  *count=0;const auto begun=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-begun).count();};
  bounded_search::Field staticfield{rectangles,nr,circles,nc};Pose root{start[0],start[1],start[2]};
  World world{staticfield,balls,nb,1e100};const double initial=std::min(staticfield.value(root),world.value(root[0]+.3*std::cos(root[2]),root[1]+.3*std::sin(root[2]),std::cos(root[2]),std::sin(root[2]),0));
  stats[0]=stats[1]=0.;stats[2]=initial;if(initial<.22-1e-8)return 2;
  world.required=std::max(.22,std::min(.27,initial-.001));stats[2]=world.required;
  bounded_search::Guide guide(staticfield,goal,world.required);
  auto heuristic=[&](const Pose&p){const double x=p[0]+.3*std::cos(p[2]),y=p[1]+.3*std::sin(p[2]);
    const double eu=std::hypot(x-goal[0],y-goal[1]),mapped=guide.value(x,y);
    return (mapped<1e19?std::max(eu,mapped):eu+5.)/.1;};
  std::array<double,7>curvatures;const double maxsteer=std::atan(.6*.5);
  for(int j=0;j<7;++j)curvatures[j]=std::tan(-maxsteer+j*(2*maxsteer/6))/.6;
  std::vector<Node>nodes;nodes.reserve(100000);nodes.push_back({root,0,0,0,0,3,-1,0,0});
  std::unordered_map<Key,Coverage,Hash> covered;covered.reserve(50000);
  covered[key(root,0,0,3)].set(0);
  std::priority_queue<timed_vehicle::Entry,std::vector<timed_vehicle::Entry>,timed_vehicle::Compare>queue;
  queue.push({heuristic(root),0.,0});int expanded=0,goalid=-1;double closest=1e100;
  bool timeout=false;
  while(!queue.empty()&&expanded<maxexpand&&elapsed()<maxwall){
    const auto e=queue.top();queue.pop();const Node node=nodes[e.id];++expanded;
    const double distance=std::hypot(node.pose[0]+.3*std::cos(node.pose[2])-goal[0],node.pose[1]+.3*std::sin(node.pose[2])-goal[1]);
    closest=std::min(closest,distance);
    if(distance<=.32&&node.velocity==0){
      bool safe=true;for(int t=node.lo;t<=node.lo+10;++t)safe &= world.safe(node.pose,t);
      if(safe){goalid=e.id;break;}
    }
    int last_depart=node.hi;
    if(node.velocity==0)while(last_depart+1<nb-11&&world.safe(node.pose,last_depart+1))++last_depart;
    auto insert=[&](int action,int gear,int st){
      if(timeout)return;
      const auto samples=motion(node,action,gear,st,curvatures);if(samples.empty())return;
      const int duration=int(std::round(samples.back().offset/dt));
      for(const auto&s:samples)if(staticfield.value(s.pose)<world.required-1e-8)return;
      Pose endpoint=samples.back().pose;endpoint[2]=bounded_search::wrap(endpoint[2]);
      const int velocity=action==3?0:1;const auto state=key(endpoint,gear,velocity,st);
      auto&seen=covered[state];int group=-1;
      auto save=[&](int hi){if(group<0)return;
        const int id=nodes.size();nodes.push_back({endpoint,group+duration,hi+duration,gear,velocity,st,e.id,action,duration});
        queue.push({(group+duration)*dt+1.45*heuristic(endpoint),(group+duration)*dt,id});group=-1;};
      for(int depart=node.lo;depart<=last_depart+1;++depart){
        if((depart&31)==0&&elapsed()>=maxwall){timeout=true;save(depart-1);return;}
        bool safe=depart<=last_depart&&depart+duration<nb-11&&!seen[depart+duration];
        if(safe)for(const auto&s:samples){
          const int tick=depart+int(std::floor((s.offset+1e-8)/dt));
          if(world.value(s.x,s.y,s.c,s.s,tick)<world.required-1e-8){safe=false;break;}
        }
        if(safe){seen.set(depart+duration);if(group<0)group=depart;}
        else save(depart-1);
      }
    };
    if(node.velocity==0){for(int gear:{1,-1})for(int st=0;st<7;++st)insert(1,gear,st);}
    else{insert(3,node.gear,node.steer);for(int st=0;st<7;++st)insert(2,node.gear,st);}
    if(timeout)break;
  }
  stats[0]=expanded;stats[1]=elapsed();stats[3]=goalid>=0;stats[4]=nodes.size();stats[5]=closest;
  if(goalid<0)return 1;
  // Pick a reachable arrival inside each parent interval. A cruising parent
  // must depart at its actual arrival; only a resting parent can wait.
  struct Chosen {int id,arrival,depart;};std::vector<Chosen> chain;
  int id=goalid,arrival=nodes[id].lo;double waiting=0.;
  while(nodes[id].parent>=0){
    const auto&n=nodes[id];const auto&parent=nodes[n.parent];const int depart=arrival-n.duration;
    const int parentarrival=parent.velocity?depart:std::min(parent.hi,depart);
    if(parentarrival<parent.lo||parentarrival>parent.hi)return 4;
    waiting+=(depart-parentarrival)*dt;chain.push_back({id,arrival,depart});id=n.parent;arrival=parentarrival;
  }
  std::reverse(chain.begin(),chain.end());
  if(waiting>40.+1e-8)return 5;
  std::vector<timed_vehicle::Sample>path;path.push_back({root,0.,0.,0,0});
  for(const auto&choice:chain){const auto&n=nodes[choice.id];const auto&parent=nodes[n.parent];
    while(path.back().time<choice.depart*dt-.05){const auto z=path.back();path.push_back({z.pose,z.time+.1,0.,z.gear,4});}
    const auto samples=motion(parent,n.action,n.gear,n.steer,curvatures);
    for(const auto&s:samples)path.push_back({s.pose,choice.depart*dt+s.offset,s.speed,s.gear,s.action});
  }
  const auto last=path.back();for(int j=1;j<=20;++j)path.push_back({last.pose,last.time+j*.1,0.,last.gear,5});
  if(int(path.size())>capacity)return 3;
  for(std::size_t i=0;i<path.size();++i){for(int j=0;j<3;++j)out[i*7+j]=path[i].pose[j];
    out[i*7+3]=path[i].time;out[i*7+4]=path[i].speed;out[i*7+5]=path[i].gear;out[i*7+6]=path[i].action;}
  *count=path.size();stats[6]=last.time;stats[7]=waiting;return 0;
}
