#include "feasible_twist.hpp"
#include <cassert>
#include <iostream>
#include <limits>
#include <random>
int main() {
  using namespace phase_feasible_rpp;
  const auto recorded=feasibleTwist(0.05832733826284523,-0.07575757575757576);
  assert(recorded.v==0.05832733826284523);
  assert(std::fabs(recorded.w/recorded.v)<=maximum_curvature+1e-12);
  assert(std::fabs(recorded.w/recorded.v+maximum_curvature)<1e-12);
  assert(feasibleTwist(0.0,0.2).w==0.0);
  assert(feasibleTwist(0.0049,-0.2).v==0.0);
  std::mt19937 gen(884);std::uniform_real_distribution<double> v(-.15,.3),w(-.4,.4);
  for(int i=0;i<100000;++i) {
    const double x=v(gen),y=w(gen);const auto a=feasibleTwist(x,y),b=feasibleTwist(a.v,a.w);
    assert(std::fabs(a.w)<=std::fabs(a.v)*maximum_curvature+1e-12);
    assert(a.v==b.v && a.w==b.w);
    if(std::fabs(x)>=.005 && std::fabs(y)<=std::fabs(x)*maximum_curvature) {
      assert(a.v==x && a.w==y);
    }
    const auto reverse=feasibleTwist(-x,-y);assert(a.v==-reverse.v && a.w==-reverse.w);
  }
  bool rejected=false;try{feasibleTwist(0.1,std::numeric_limits<double>::quiet_NaN());}
  catch(const std::domain_error&){rejected=true;}assert(rejected);
  std::cout<<"SAVED_COMMAND_RED_TO_GREEN_AND_100000_CONTRACT_CASES_PASS\n";
}
