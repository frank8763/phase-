// Experimental MPPI engineering sampler: compare white noise with constant
// horizon yaw perturbations, same batch means, sampled first-step distribution.
// Never canonical upstream MPPI; gamma=0 for both avoids an invalid white-noise
// regularizer for the correlated variant. Physical deployment is forbidden.
#include <xtensor/xtensor.hpp>
#include <dlfcn.h>
#include <vector>
#include <string>
#include <cstdio>
#include <cstdlib>
#include <cmath>
struct State {xt::xtensor<float,2>vx,vy,wz,cvx,cvy,cwz;};
using Update=void(*)(const void *,void *);
extern "C" void coherent_update(const void*,void*) asm("_ZNK4mppi9Optimizer21updateStateVelocitiesERNS_6models5StateE");
extern "C" void coherent_update(const void *self,void *opaque){
  static void *lib=dlopen("/opt/ros/jazzy/lib/libmppi_controller.so",RTLD_NOW|RTLD_NOLOAD);
  static auto original=reinterpret_cast<Update>(dlsym(lib,"_ZNK4mppi9Optimizer21updateStateVelocitiesERNS_6models5StateE"));
  if(!original)std::abort();
  auto *state=static_cast<State*>(opaque);
  if(state->cwz.shape(0)!=1000 || state->cwz.shape(1)!=56)std::abort();
  const char *configured=std::getenv("PHASE_COHERENT_NOISE");
  bool enabled=configured && std::string(configured)=="1";
  std::vector<double> mean(56,0.);
  for(std::size_t j=0;j<56;++j)for(std::size_t i=0;i<1000;++i)mean[j]+=state->cwz(i,j)/1000.;
  double before=0.,after=0.;
  for(std::size_t i=0;i<1000;++i){
    double sum=0.,latent=state->cwz(i,0)-mean[0];
    for(std::size_t j=0;j<56;++j)sum+=state->cwz(i,j)-mean[j];
    before+=sum*sum*.05*.05/1000.;
    if(enabled)for(std::size_t j=0;j<56;++j)state->cwz(i,j)=float(mean[j]+latent);
    sum=0.;for(std::size_t j=0;j<56;++j)sum+=state->cwz(i,j)-mean[j];
    after+=sum*sum*.05*.05/1000.;
  }
  std::fprintf(stderr,"[DEBUG-1319] {\"coherent\":%s,\"before_yaw_noise_sd\":%.17g,\"after_yaw_noise_sd\":%.17g}\n",enabled?"true":"false",std::sqrt(before),std::sqrt(after));std::fflush(stderr);
  original(self,opaque);
}
