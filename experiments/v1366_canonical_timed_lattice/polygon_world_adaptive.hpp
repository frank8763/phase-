// Full rectangle-to-causal-outer-polygon clearance. Actor radius is ALREADY
// in polygon support; do not subtract/add it again. No simulator dependencies.
struct PolygonWorld {
  const double*vertices;const int*counts;int nb;double required;
  double value(double x,double y,double c,double s,int index)const{
    if(index<0||index>=nb)return -1e100;
    const int n=counts[index];if(n<3||n>16)return -1e100;const double*p=vertices+index*32;
    double separation=-1e100;
    auto axis=[&](double nx,double ny){
      double low=1e100,high=-1e100;
      for(int j=0;j<n;++j){const double q=nx*(p[2*j]-x)+ny*(p[2*j+1]-y);low=std::min(low,q);high=std::max(high,q);}
      const double radius=.44*std::abs(nx*c+ny*s)+.375*std::abs(-nx*s+ny*c);
      separation=std::max({separation,low-radius,-radius-high});
    };
    axis(c,s);axis(-s,c);
    for(int j=0;j<n;++j){const int next=(j+1)%n;const double dx=p[2*next]-p[2*j],dy=p[2*next+1]-p[2*j+1];
      const double length=std::hypot(dx,dy);if(length<1e-12)return -1e100;axis(-dy/length,dx/length);
      if(separation>=required+.02)return separation;
    }
    if(separation<=0.)return 0.;
    double distance=1e100;
    for(int j=0;j<n;++j){const double dx=p[2*j]-x,dy=p[2*j+1]-y;
      distance=std::min(distance,std::hypot(std::max(std::abs(dx*c+dy*s)-.44,0.),std::max(std::abs(-dx*s+dy*c)-.375,0.)));
    }
    for(int sx:{-1,1})for(int sy:{-1,1}){const double cx=x+c*sx*.44-s*sy*.375,cy=y+s*sx*.44+c*sy*.375;
      for(int j=0;j<n;++j){const int next=(j+1)%n;const double dx=p[2*next]-p[2*j],dy=p[2*next+1]-p[2*j+1];
        const double vx=cx-p[2*j],vy=cy-p[2*j+1];const double t=std::clamp((vx*dx+vy*dy)/(dx*dx+dy*dy),0.,1.);
        distance=std::min(distance,std::hypot(vx-t*dx,vy-t*dy));
      }
    }
    return distance;
  }
  bool safe(const bounded_search::Pose&p,int tick)const{
    const double c=std::cos(p[2]),s=std::sin(p[2]);return value(p[0]+.3*c,p[1]+.3*s,c,s,tick)>=required-1e-8;
  }
};
