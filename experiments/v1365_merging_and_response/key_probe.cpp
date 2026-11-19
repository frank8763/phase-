// Regression seam executes both the original key function and repaired key.
#include "../v1358_terminal_contract/search.cpp"
#include "exact_state.hpp"
extern "C" int key_equivalence(const double*a,const double*b,int gear,int velocity,int steer){
  bounded_search::Pose pa{a[0],a[1],a[2]},pb{b[0],b[1],b[2]};
  const bool old=bounded_search::key(pa,gear)==bounded_search::key(pb,gear);
  const bool now=exact_vehicle_key(a[0],a[1],a[2],gear,velocity,steer)==exact_vehicle_key(b[0],b[1],b[2],gear,velocity,steer);
  return int(old)+2*int(now);
}
