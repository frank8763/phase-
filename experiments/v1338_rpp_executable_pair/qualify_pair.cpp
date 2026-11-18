#include "project_pair.hpp"
#include <cassert>
#include <iostream>
#include <random>
int main() {
  double v,w;unsigned rows=0,changed=0;
  while(std::cin>>v>>w){
    auto p=phase_rpp::project(v,w);
    assert(std::abs(p.v)<=.1&&std::abs(p.w)<=std::abs(p.v)/1.32+1e-15);
    changed+=p.v!=v||p.w!=w;++rows;
  }
  std::mt19937 rng(1338);std::uniform_real_distribution<double>d(-.2,.2);
  for(unsigned i=0;i<100000;++i){auto p=phase_rpp::project(d(rng),d(rng));
    assert(std::abs(p.v)<=.1&&std::abs(p.w)<=std::abs(p.v)/1.32+1e-15);
    if(std::abs(p.v)<.005)assert(p.v==0&&p.w==0);
  }
  assert(phase_rpp::project(0.,.1).w==0.);
  bool rejected=false;try{phase_rpp::project(NAN,0.);}catch(...){rejected=true;}assert(rejected);
  std::cout<<"{\"saved_rows\":"<<rows<<",\"changed_rows\":"<<changed<<",\"random_pairs\":100000,\"passed\":true}\n";
}
