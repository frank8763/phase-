// Optimistic orientation-free time guide. Never used to approve/prune edges.
#include <algorithm>
#include <cmath>
#include <vector>

struct TimeGuide {
  static constexpr int side=101,cells=side*side;
  static constexpr float infinity=1e8f;
  std::vector<float> values;int count;
  TimeGuide(const bounded_search::Field&field,const double*boxes,int nb,const double*goal,double margin):values(nb*cells,infinity),count(nb){
    std::vector<unsigned char> staticfree(cells,0),terminal(cells,0);
    for(int y=0;y<side;++y)for(int x=0;x<side;++x){const int id=y*side+x;const double px=-5.+x*.1,py=-5.+y*.1;
      staticfree[id]=field.point(px,py)>=.375+margin-1e-8;
      terminal[id]=std::hypot(px-goal[0],py-goal[1])<=.32;
    }
    for(int tick=nb-1;tick>=0;--tick){const double*b=boxes+4*tick;
      for(int y=0;y<side;++y)for(int x=0;x<side;++x){const int id=y*side+x;if(!staticfree[id])continue;
        const double dx=std::max(std::abs(-5.+x*.1-b[0])-b[2],0.),dy=std::max(std::abs(-5.+y*.1-b[1])-b[3],0.);
        if(std::hypot(dx,dy)<.375+.10+margin-1e-8)continue;
        float best=terminal[id]?0.f:infinity;
        if(tick+1<nb)best=std::min(best,1.f+values[(tick+1)*cells+id]);
        for(int oy=-1;oy<=1;++oy)for(int ox=-1;ox<=1;++ox){
          if(!ox&&!oy)continue;const int xx=x+ox,yy=y+oy,travel=ox&&oy?7:5;
          if(xx<0||xx>=side||yy<0||yy>=side||tick+travel>=nb)continue;
          best=std::min(best,float(travel)+values[(tick+travel)*cells+yy*side+xx]);
        }
        values[tick*cells+id]=best;
      }
    }
  }
  double value(double x,double y,int tick)const{
    const int ix=int(std::nearbyint((x+5.)/.1)),iy=int(std::nearbyint((y+5.)/.1));
    if(ix<0||ix>=side||iy<0||iy>=side||tick<0||tick>=count)return 1e100;
    const double result=values[tick*cells+iy*side+ix];return result>=infinity?1e100:result*.2;
  }
};
