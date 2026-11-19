// Read-only seams for existing compiled geometry and guide ordering.
#include "interval_kinodynamic.cpp"

extern "C" void box_clearance_probe(const double*poses,int count,const double*box,
                                    double requested,double*output){
  bounded_search::Field empty{nullptr,0,nullptr,0};
  interval_kinodynamic_vehicle::World world{empty,box,1,requested};
  for(int i=0;i<count;++i){const double*p=poses+i*3,c=std::cos(p[2]),s=std::sin(p[2]);
    output[i]=world.value(p[0]+.3*c,p[1]+.3*s,c,s,0);
  }
}

extern "C" void time_guide_probe(const double*rect,int nr,const double*circles,int nc,
    const double*boxes,int count,const double*body,const double*goal,double margin,double*output){
  bounded_search::Field field{rect,nr,circles,nc};TimeGuide guide(field,boxes,count,goal,margin);
  for(int tick=0;tick<count;++tick)output[tick]=guide.value(body[0],body[1],tick);
}
