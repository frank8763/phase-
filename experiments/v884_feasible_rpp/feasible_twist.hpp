// Native body-command curvature feasibility only, no collision/model interface.
#pragma once
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace phase_feasible_rpp {
constexpr double maximum_curvature = 0.7587703849338058;
struct Twist { double v; double w; };
inline Twist feasibleTwist(double v, double w) {
  if (!std::isfinite(v) || !std::isfinite(w)) {
    throw std::domain_error("NONFINITE_NOMINAL_TWIST");
  }
  if (std::fabs(v) < 0.005) { return {0.0, 0.0}; }
  const double limit = std::fabs(v) * maximum_curvature;
  return {v, std::clamp(w, -limit, limit)};
}
}
