// Canonical rest-state graph. Every translation/heading edge has an endpoint
// witness; no coarse continuous-pose label is substituted for another pose.
#include "../v1365_merging_and_response/slew_search.cpp"
#include "polygon_world_adaptive.hpp"

namespace adaptive_polygon_graph {
using Pose=bounded_search::Pose;
struct Key {int x,y,h,g;bool operator==(const Key&o)const{return x==o.x&&y==o.y&&h==o.h&&g==o.g;}};
struct Hash {std::size_t operator()(const Key&k)const{return bounded_search::Hash{}({k.x,k.y,k.h,k.g});}};
struct Edge {int first,last,dx,dy,gear,offset,count,duration,rest;};
struct Config {Key key;Pose pose;std::array<int,401>interval;std::vector<int>labels;};
struct Node {int config,t,wait,parent,edge,depart,gearhold;};
struct TimedPose {Pose pose;double t,v,steering,padding;};
struct EdgeCache {bool valid=false;std::vector<TimedPose>poses;};
}

extern "C" int plan_graph_adaptive(const double*rectangles,int nr,const double*circles,int nc,
    const double*body,const double*goal,const double*boxes,int nb,const double*headings,
    const double*metadata,int ne,const double*samples,int initial_gear,
    int maxexpand,double maxwall,double*out,int capacity,int*count,double*stats,const double*polyvertices,const int*polycounts){
  using namespace adaptive_polygon_graph;
  *count=0;const auto begun=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-begun).count();};
  bounded_search::Field field{rectangles,nr,circles,nc};PolygonWorld world{polyvertices,polycounts,nb,1e100};
  const double yaw0=body[2],c0=std::cos(yaw0),s0=std::sin(yaw0);
  const double ox=body[0]-.3*c0,oy=body[1]-.3*s0;
  const Pose root{ox,oy,yaw0};
  const double initial=std::min(field.value(root),world.value(body[0],body[1],c0,s0,0));
  stats[0]=stats[1]=0.;stats[2]=initial;if(initial<.22-1e-8)return 2;
  const double required=std::max(.22,std::min(.27,initial-.001));world.required=required;
  stats[2]=required;if(initial<world.required-1e-8)return 6;
  TimeGuide guide(field,boxes,nb,goal,required);
  std::vector<Edge>edges;std::array<std::vector<int>,17>outgoing;
  for(int j=0;j<ne;++j){const double*m=metadata+9*j;
    edges.push_back({int(m[0]),int(m[1]),int(m[2]),int(m[3]),int(m[4]),int(m[5]),int(m[6]),int(m[7]),int(m[8])});
    outgoing[edges.back().first].push_back(j);
  }
  std::vector<Config>configs;configs.reserve(30000);std::unordered_map<Key,int,Hash>ids;ids.reserve(30000);
  std::vector<Node>nodes;nodes.reserve(100000);
  auto get_config=[&](Key key){
    const auto found=ids.find(key);if(found!=ids.end())return found->second;
    const double x=key.x*.2,y=key.y*.2;const double angle=yaw0+(key.h==16?0.:headings[key.h]);
    const Pose pose{ox+c0*x-s0*y,oy+s0*x+c0*y,angle};
    Config cfg;cfg.key=key;cfg.pose=pose;cfg.interval.fill(-1);
    if(field.value(pose)>=world.required-1e-8){int interval=-1;bool previous=false;
      for(int t=0;t<nb;++t){const bool safe=world.safe(pose,t);if(safe&&!previous)++interval;
        cfg.interval[t]=safe?interval:-1;previous=safe;}
    }
    const int index=configs.size();ids.emplace(key,index);configs.push_back(std::move(cfg));return index;
  };
  auto heuristic=[&](const Pose&p,int tick){const double x=p[0]+.3*std::cos(p[2]),y=p[1]+.3*std::sin(p[2]);
    const double distance=std::hypot(x-goal[0],y-goal[1])/.1;const double timed=guide.value(x,y,tick);
    return timed<1e99?std::max(distance,timed):distance+20.;};
  const int start=get_config({0,0,16,initial_gear});if(configs[start].interval[0]<0)return 6;
  nodes.push_back({start,0,0,-1,-1,0,0});configs[start].labels.push_back(0);
  std::priority_queue<timed_vehicle::Entry,std::vector<timed_vehicle::Entry>,timed_vehicle::Compare>queue;
  queue.push({heuristic(root,0),0.,0});
  std::unordered_map<std::uint64_t,EdgeCache>cache;cache.reserve(10000);int expanded=0,goalid=-1;double closest=1e100;
  auto dominated=[&](int config,int arrival,int wait){const auto&cfg=configs[config];
    for(int id:cfg.labels){const auto&old=nodes[id];
      if(cfg.interval[old.t]!=cfg.interval[arrival])continue;
      if(old.t<=arrival&&old.wait+arrival-old.t<=wait)return true;
    }return false;};
  while(!queue.empty()&&expanded<maxexpand&&elapsed()<maxwall){
    const auto top=queue.top();queue.pop();const Node node=nodes[top.id];const Config current=configs[node.config];++expanded;
    const double distance=std::hypot(current.pose[0]+.3*std::cos(current.pose[2])-goal[0],current.pose[1]+.3*std::sin(current.pose[2])-goal[1]);closest=std::min(closest,distance);
    if(distance<=.32&&current.key.h!=16&&node.t+10<nb){bool safe=true;
      for(int t=node.t;t<=node.t+10;++t)safe &= current.interval[t]==current.interval[node.t];
      if(safe){goalid=top.id;break;}
    }
    int last=node.t;
    while(last+1<nb&&current.interval[last+1]==current.interval[node.t])++last;
    for(int edgeid:outgoing[current.key.h]){
      if(elapsed()>=maxwall)break;const Edge&e=edges[edgeid];
      const std::uint64_t cachekey=(std::uint64_t(node.config)<<32)|std::uint64_t(edgeid);
      auto found=cache.find(cachekey);
      if(found==cache.end()){
        EdgeCache value;value.valid=true;value.poses.reserve(e.count);
        for(int i=0;i<e.count;++i){const double*p=samples+(e.offset+i)*6;
          const double x=current.key.x*.2+p[0],y=current.key.y*.2+p[1];
          const Pose pose{ox+c0*x-s0*y,oy+s0*x+c0*y,yaw0+p[2]};
          double vmax=std::abs(p[4]);
          if(i>0)vmax=std::max(vmax,std::abs(samples[(e.offset+i-1)*6+4]));
          if(i+1<e.count)vmax=std::max(vmax,std::abs(samples[(e.offset+i+1)*6+4]));
          const double padding=vmax*(1.+std::hypot(.74,.375)*.50)*.025+2e-8;
          if(field.value(pose)<world.required+padding-1e-8){value.valid=false;value.poses.clear();break;}
          value.poses.push_back({pose,p[3],p[4],p[5],padding});
        }
        found=cache.emplace(cachekey,std::move(value)).first;
      }
      const EdgeCache&course=found->second;if(!course.valid)continue;
      const int child=get_config({current.key.x+e.dx,current.key.y+e.dy,e.last,e.gear});
      const int gearhold=current.key.g&&current.key.g!=e.gear?10:0;
      const int total=e.duration+gearhold;std::vector<int>visited_intervals;
      for(int depart=node.t;depart<=last&&depart+total+10<nb;++depart){
        if((depart&15)==0&&elapsed()>=maxwall)break;
        const int arrival=depart+total,waiting=node.wait+depart-node.t+gearhold+e.rest;
        if(waiting>200||depart+gearhold>last)break;
        const int interval=configs[child].interval[arrival];
        if(interval<0||std::find(visited_intervals.begin(),visited_intervals.end(),interval)!=visited_intervals.end())continue;
        if(dominated(child,arrival,waiting))continue;
        bool safe=true;
        for(const auto&p:course.poses){const int tick=depart+gearhold+int(std::floor((p.t+1e-8)/.2));
          const double co=std::cos(p.pose[2]),si=std::sin(p.pose[2]);
          if(world.value(p.pose[0]+.3*co,p.pose[1]+.3*si,co,si,tick)<world.required+p.padding-1e-8){safe=false;break;}
        }
        if(!safe)continue;
        visited_intervals.push_back(interval);const int id=nodes.size();nodes.push_back({child,arrival,waiting,top.id,edgeid,depart,gearhold});
        configs[child].labels.push_back(id);queue.push({arrival*.2+1.45*heuristic(configs[child].pose,arrival),arrival*.2,id});
      }
    }
  }
  stats[0]=expanded;stats[1]=elapsed();stats[3]=goalid>=0;stats[4]=nodes.size();stats[5]=closest;
  stats[8]=configs.size();stats[9]=cache.size();if(goalid<0)return 1;
  std::vector<int>chain;for(int id=goalid;nodes[id].parent>=0;id=nodes[id].parent)chain.push_back(id);std::reverse(chain.begin(),chain.end());
  int nout=0;
  auto emit=[&](const Pose&pose,double t,double speed,double steering,int gear,int action,int node,int edge){
    if(nout>=capacity)return false;double*p=out+10*nout++;
    for(int j=0;j<3;++j)p[j]=pose[j];p[3]=t;p[4]=speed;p[5]=steering;p[6]=gear;p[7]=action;p[8]=node;p[9]=edge;return true;};
  const double rootsteering=samples[edges[outgoing[16].front()].offset*6+5];emit(root,0.,0.,rootsteering,initial_gear,0,0,-1);
  double previous_time=0.;
  for(int id:chain){const Node&node=nodes[id];const Node&parent=nodes[node.parent];const Config&cfg=configs[parent.config];
    const Edge&e=edges[node.edge];const double motionstart=(node.depart+node.gearhold)*.2;
    const double steering=cfg.key.h==16?rootsteering:0.;
    while(previous_time+.049999<motionstart){previous_time+=.05;if(!emit(cfg.pose,previous_time,0.,steering,cfg.key.g,4,id,node.edge))return 3;}
    const auto&course=cache[(std::uint64_t(parent.config)<<32)|std::uint64_t(node.edge)];
    for(int i=1;i<int(course.poses.size());++i){const auto&p=course.poses[i];previous_time=motionstart+p.t;
      if(!emit(p.pose,previous_time,p.v,p.steering,e.gear,1,id,node.edge))return 3;}
  }
  stats[6]=nodes[goalid].t*.2;stats[7]=nodes[goalid].wait*.2;*count=nout;return 0;
}

extern "C" void polygon_adaptive_values_probe(const double*poses,int count,const double*vertices,int n,double margin,double*output){
  PolygonWorld world{vertices,&n,1,margin};
  for(int i=0;i<count;++i){const double*p=poses+i*3,c=std::cos(p[2]),s=std::sin(p[2]);output[i]=world.value(p[0]+.3*c,p[1]+.3*s,c,s,0);}
}
