// Phase engineering adaptation; not a new MPPI derivation or safety theorem.
#pragma once
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace phase_predictive {
constexpr float K=1.0f/1.32f;
inline float projected_v(float v,int gear,float lo,float hi) {
 if(!std::isfinite(v)||!std::isfinite(lo)||!std::isfinite(hi)||(gear!=1&&gear!=-1))throw std::runtime_error("INVALID_EXECUTABLE_PROJECTION");
 return gear==1?std::clamp(v,0.0f,hi):std::clamp(v,lo,0.0f);
}
template<class State> unsigned project_samples(State &s,int gear,float lo,float hi) {
 unsigned changed=0;
 for(unsigned i=0;i<s.cvx.shape(0);++i)for(unsigned j=0;j<s.cvx.shape(1);++j){
  float &v=s.cvx(i,j),&w=s.cwz(i,j);if(!std::isfinite(w))throw std::runtime_error("NONFINITE_SAMPLED_YAW");
  const float pv=projected_v(v,gear,lo,hi),pw=std::clamp(w,-std::abs(pv)*K,std::abs(pv)*K);
  changed+=v!=pv||w!=pw;v=pv;w=pw;
 }
 // Current measured body state (column0) remains untouched. Future state and
 // candidate controls now describe the SAME realizable command sequence.
 for(unsigned i=0;i<s.vx.shape(0);++i)for(unsigned j=1;j<s.vx.shape(1);++j){s.vx(i,j)=s.cvx(i,j-1);s.wz(i,j)=s.cwz(i,j-1);}
 return changed;
}
template<class Sequence> void project_sequence(Sequence &s,int gear,float lo,float hi){
 for(unsigned j=0;j<s.vx.size();++j){s.vx(j)=projected_v(s.vx(j),gear,lo,hi);if(!std::isfinite(s.wz(j)))throw std::runtime_error("NONFINITE_FILTERED_YAW");s.wz(j)=std::clamp(s.wz(j),-std::abs(s.vx(j))*K,std::abs(s.vx(j))*K);}
}
}
