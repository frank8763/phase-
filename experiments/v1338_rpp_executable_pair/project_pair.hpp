#pragma once
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace phase_rpp {
struct Pair {double v,w;};
inline Pair project(double v,double w) {
  if(!std::isfinite(v)||!std::isfinite(w))throw std::runtime_error("NONFINITE_RPP_PAIR");
  v=std::clamp(v,-.1,.1);
  if(std::abs(v)<.005)return {0.,0.};
  const double limit=std::abs(v)/1.32;
  return {v,std::clamp(w,-limit,limit)};
}
}
