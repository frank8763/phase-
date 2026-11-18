// Diagnostic ABI bridge for the pinned ROS message layout; never changes control.
// Time: int32 sec,uint32 nanosec; Header: Time,std::string;
// TwistStamped: Header,Vector3 linear,Vector3 angular. Exact upstream IDL layout.
#include <cstdint>
#include <string>
#include <dlfcn.h>
#include <cstdio>
#include <cmath>
#include <cstdlib>
struct Stamp { std::int32_t sec; std::uint32_t nanosec; };
struct Header { Stamp stamp; std::string frame_id; };
struct Vector { double x,y,z; };
struct Twist { Vector linear,angular; };
struct Stamped { Header header; Twist twist; };
using Optimize = void (*)(void *);
using Getter = Stamped (*)(void *,const Stamp &);
extern "C" void trace_optimize(void *self) asm("_ZN4mppi9Optimizer8optimizeEv");
extern "C" void trace_optimize(void *self) {
    static auto original = reinterpret_cast<Optimize>(dlsym(RTLD_NEXT,"_ZN4mppi9Optimizer8optimizeEv"));
    static auto getter = reinterpret_cast<Getter>(dlsym(RTLD_NEXT,"_ZN4mppi9Optimizer29getControlFromSequenceAsTwistERKN18builtin_interfaces3msg5Time_ISaIvEEE"));
    if (!original || !getter) std::abort();
    original(self);
    const Stamp stamp{0,0};
    auto value = getter(self,stamp);
    if (value.header.frame_id != "base_link" || !std::isfinite(value.twist.linear.x) || !std::isfinite(value.twist.angular.z)) std::abort();
    std::fprintf(stderr,"[DEBUG-1312] {\"optimized_unfiltered_v\":%.17g,\"optimized_unfiltered_w\":%.17g,\"frame_layout_validated\":true}\n",value.twist.linear.x,value.twist.angular.z);
    std::fflush(stderr);
}
