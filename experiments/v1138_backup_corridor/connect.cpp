// Diagnostic rigid-body configuration graph, not a car controller.
#include "../v1093_causal_space_time/search.cpp"
#include <functional>
extern "C" int configuration_path(const double*rect,int nr,const double*circles,int nc,
 const double*support,int nb,double bin,const double*root,const double*goal,double cell,int headings,
 int fullcycle,double maxwall,double*out,int capacity,int*count,double*stats){
 auto begun=std::chrono::steady_clock::now();auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-begun).count();};
 Geometry geom{rect,circles,fullcycle?support:nullptr,nr,nc,nb,0.,bin};std::vector<Polygon>polys;
 if(fullcycle){for(int i=0;i<=nb;i++)polys.push_back(polygon(support+16*i));geom.polys=&polys;}
 int xmin=int(std::ceil((-5-root[0])/cell)),xmax=int(std::floor((5-root[0])/cell));
 int ymin=int(std::ceil((-5-root[1])/cell)),ymax=int(std::floor((5-root[1])/cell));
 int nx=xmax-xmin+1,ny=ymax-ymin+1,size=nx*ny*headings;double da=2*pi/headings;
 auto id=[&](int x,int y,int a){return (a*ny+y)*nx+x;};
 auto pose=[&](int i,double*q){int x=i%nx,y=(i/nx)%ny,a=i/(nx*ny);q[0]=root[0]+(x+xmin)*cell;q[1]=root[1]+(y+ymin)*cell;q[2]=root[2]+a*da;};
 std::vector<double> clearance(size,std::numeric_limits<double>::quiet_NaN());std::vector<float>cost(size,std::numeric_limits<float>::infinity());std::vector<int>parent(size,-2);
 auto value=[&](int i){if(std::isnan(clearance[i])){double q[8]={};pose(i,q);clearance[i]=geom.value(q,0,fullcycle)-.000002;}return clearance[i];};
 struct Q{double f,g;int i;bool operator<(const Q&o)const{return f>o.f;}};
 auto heuristic=[&](int i){double q[3];pose(i,q);return std::max(0.,std::hypot(q[0]-goal[0],q[1]-goal[1])-.025)+rho*std::max(0.,std::abs(std::atan2(std::sin(q[2]),std::cos(q[2])))-.1);};
 int source=id(-xmin,-ymin,0);*count=0;if(value(source)<required){stats[0]=0;stats[1]=elapsed();stats[2]=value(source);return 2;}
 std::priority_queue<Q>queue;cost[source]=0.;parent[source]=-1;queue.push({heuristic(source),0.,source});int expanded=0,rejected=0,found=-1;double closest=heuristic(source);
 while(!queue.empty()&&elapsed()<maxwall){
  auto q=queue.top();queue.pop();if(q.g>cost[q.i]+1e-5)continue;expanded++;closest=std::min(closest,heuristic(q.i));
  if(heuristic(q.i)<=1e-12){found=q.i;break;}
  int x=q.i%nx,y=(q.i/nx)%ny,a=q.i/(nx*ny);double p[3];pose(q.i,p);
  for(int action=0;action<6;action++){
   int xx=x,yy=y,aa=a;double length=cell,angle=0.;
   if(action==0)xx--;if(action==1)xx++;if(action==2)yy--;if(action==3)yy++;
   if(action>=4){aa=(a+(action==4?1:headings-1))%headings;length=0.;angle=action==4?da:-da;}
   if(xx<0||xx>=nx||yy<0||yy>=ny)continue;int next=id(xx,yy,aa);if(value(next)<required)continue;
   // Exact midpoint plus distance-Lipschitz/Hausdorff displacement bound
   // certifies the full rigid interpolation, not merely free endpoints.
   double mid[8]={};mid[0]=p[0]+(xx-x)*cell*.5;mid[1]=p[1]+(yy-y)*cell*.5;mid[2]=p[2]+angle*.5;
   double reserve=length*.5+rho*std::abs(angle)*.5;
   if(geom.value(mid,0,fullcycle)-.000002-reserve<required){rejected++;continue;}
   double g=q.g+length+rho*std::abs(angle);if(g>=cost[next]-1e-6)continue;
   cost[next]=g;parent[next]=q.i;queue.push({g+heuristic(next),g,next});
  }
 }
 stats[0]=expanded;stats[1]=elapsed();stats[2]=closest;stats[3]=rejected;stats[4]=size;
 if(found<0)return queue.empty()?1:5;
 std::vector<int>path;for(int i=found;i!=-1;i=parent[i])path.push_back(i);std::reverse(path.begin(),path.end());
 if(int(path.size())>capacity)return 3;
 for(size_t j=0;j<path.size();j++)pose(path[j],out+3*j);*count=path.size();stats[5]=cost[found];return 0;
}
