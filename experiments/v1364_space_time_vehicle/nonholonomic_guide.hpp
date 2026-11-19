// Reeds-Shepp ordering only; never certifies an edge or changes the goal gate.
struct NonholonomicGuide {
  std::vector<bounded_search::Pose> targets;
  std::unordered_map<bounded_search::Key,double,bounded_search::Hash> cache;
  NonholonomicGuide(const bounded_search::Field&field,const double*goal,double margin){
    constexpr double pi=bounded_search::pi;
    for(int h=0;h<16;++h){const double yaw=h*2*pi/16;double best=-1e100;bounded_search::Pose selected{};bool found=false;
      for(int i=0;i<9;++i){const double a=(i-1)*2*pi/8;
        const double x=goal[0]+(i?.32*std::cos(a):0.),y=goal[1]+(i?.32*std::sin(a):0.);
        const bounded_search::Pose p{x-.3*std::cos(yaw),y-.3*std::sin(yaw),yaw};
        const double clearance=field.value(p);
        if(clearance>=margin-1e-8&&(!found||clearance>best)){selected=p;best=clearance;found=true;}
      }
      if(found)targets.push_back(selected);
    }
    cache.reserve(30000);
  }
  double value(const bounded_search::Pose&p){
    const auto k=bounded_search::key(p,0);const auto old=cache.find(k);if(old!=cache.end())return old->second;
    const double c=std::cos(p[2]),s=std::sin(p[2]);double distance=1e100;
    for(const auto&t:targets){const double dx=t[0]-p[0],dy=t[1]-p[1];
      const auto solution=::getPath((c*dx+s*dy)*.5,(-s*dx+c*dy)*.5,t[2]-p[2]);
      distance=std::min(distance,solution.length()/.5);
    }
    cache[k]=distance;return distance;
  }
};
