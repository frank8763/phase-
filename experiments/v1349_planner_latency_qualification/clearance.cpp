// Same signed full-footprint equations as V855 exact_footprint.py.
// Pure distance arithmetic. No simulator, planner, state or control writes.
#include <algorithm>
#include <cmath>
#include <cstddef>

static double norm(double x, double y) { return std::sqrt(x*x + y*y); }

extern "C" void footprint_values(
    const double* poses, std::size_t n, double hx, double hy,
    double ox, double oy, double lower, double upper,
    const double* rectangles, std::size_t nr,
    const double* circles, std::size_t nc,
    const double* points, std::size_t np, double sensor_extra,
    double* output) {
  constexpr int sx[4] = {-1, -1, 1, 1};
  constexpr int sy[4] = {-1, 1, 1, -1};
  for (std::size_t i=0; i<n; ++i) {
    const double* p=poses+3*i;
    const double c=std::cos(p[2]), s=std::sin(p[2]);
    const double ac=std::abs(c), as=std::abs(s);
    const double cx=p[0]+(c*ox-s*oy), cy=p[1]+(s*ox+c*oy);
    const double ex=ac*hx+as*hy, ey=as*hx+ac*hy;
    double result=std::min({cx-ex-lower, upper-cx-ex, cy-ey-lower, upper-cy-ey});
    for (std::size_t j=0; j<nr; ++j) {
      const double* r=rectangles+4*j;
      const double dx=r[0]-cx, dy=r[1]-cy, rx=r[2], ry=r[3];
      const double sep=std::max({std::abs(dx)-rx-ex, std::abs(dy)-ry-ey,
          std::abs(dx*c+dy*s)-hx-rx*ac-ry*as,
          std::abs(-dx*s+dy*c)-hy-rx*as-ry*ac});
      double distance=sep;
      if (sep>0.) {
        double d1=1e100, d2=1e100;
        for (int k=0; k<4; ++k) {
          const double lx=sx[k]*hx, ly=sy[k]*hy;
          const double qx=cx+(c*lx-s*ly), qy=cy+(s*lx+c*ly);
          d1=std::min(d1,norm(std::max(std::abs(qx-r[0])-rx,0.),
                              std::max(std::abs(qy-r[1])-ry,0.)));
          const double vx=(r[0]+sx[k]*rx)-cx, vy=(r[1]+sy[k]*ry)-cy;
          d2=std::min(d2,norm(std::max(std::abs(vx*c+vy*s)-hx,0.),
                              std::max(std::abs(-vx*s+vy*c)-hy,0.)));
        }
        distance=std::min(d1,d2);
      }
      result=std::min(result,distance);
    }
    for (int source=0; source<2; ++source) {
      const std::size_t count=source==0 ? nc : np;
      const std::size_t stride=source==0 ? 3 : 2;
      const double* base=source==0 ? circles : points;
      for (std::size_t j=0; j<count; ++j) {
        const double* q=base+stride*j;
        const double dx=q[0]-cx, dy=q[1]-cy;
        const double rx=std::abs(dx*c+dy*s)-hx;
        const double ry=std::abs(-dx*s+dy*c)-hy;
        const double inside=std::max(rx,ry);
        const double distance=inside<=0. ? inside : norm(std::max(rx,0.),std::max(ry,0.));
        result=std::min(result,distance-(source==0 ? q[2] : sensor_extra));
      }
    }
    output[i]=result;
  }
}
