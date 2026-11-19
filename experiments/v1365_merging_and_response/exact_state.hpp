// Conservative equality for continuous-pose labels. Bins may order a search;
// sharing a bin is never sufficient to reject another pose's arrival times.
#include <array>
#include <cstdint>
#include <cstring>

struct ExactVehicleKey {
  std::uint64_t x,y,h;int gear,velocity,steer;
  bool operator==(const ExactVehicleKey&o)const{
    return x==o.x&&y==o.y&&h==o.h&&gear==o.gear&&velocity==o.velocity&&steer==o.steer;
  }
};
struct ExactVehicleHash {
  std::size_t operator()(const ExactVehicleKey&k)const{
    std::uint64_t h=1469598103934665603ULL;
    for(std::uint64_t x:std::array<std::uint64_t,6>{k.x,k.y,k.h,std::uint64_t(k.gear+1),std::uint64_t(k.velocity),std::uint64_t(k.steer)}){
      h^=x;h*=1099511628211ULL;
    }
    return h;
  }
};
inline std::uint64_t vehicle_double_identity(double value){
  // Signed zero is the only collapsed IEEE representation. No positional or
  // angular tolerance may silently remove a continuously distinct label.
  if(value==0.)value=0.;
  std::uint64_t bits;std::memcpy(&bits,&value,sizeof bits);return bits;
}
inline ExactVehicleKey exact_vehicle_key(double x,double y,double h,int gear,int velocity,int steer){
  return {vehicle_double_identity(x),vehicle_double_identity(y),vehicle_double_identity(h),gear,velocity,steer};
}
