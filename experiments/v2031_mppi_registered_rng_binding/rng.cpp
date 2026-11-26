// Seed provenance only: original xtensor engine, no optimizer/noise changes.
#include <xtensor/xrandom.hpp>
#include <cstdint>
#include <dlfcn.h>
#include <cstring>
namespace {bool seeded=false;unsigned long long chosen=0;}
extern "C" {
int phase_mppi_rng_seed(unsigned long long seed) {
 if(seeded||seed>UINT32_MAX)return -1;
 void* core=dlopen("/opt/ros/jazzy/lib/libmppi_controller.so",RTLD_NOW|RTLD_NOLOAD);
 if(!core)return -2;
 void* original=dlsym(core,"_ZZN2xt6random25get_default_random_engineEvE2mt");
 auto* local=&xt::random::get_default_random_engine();
 if(!original||original!=static_cast<void*>(local)){dlclose(core);return -3;}
 local->seed(static_cast<xt::random::seed_type>(seed));chosen=seed;seeded=true;
 dlclose(core);return 0;
}
unsigned long long phase_mppi_rng_chosen_seed(){return chosen;}
unsigned long long phase_mppi_rng_engine_address(){return reinterpret_cast<unsigned long long>(&xt::random::get_default_random_engine());}
int phase_mppi_rng_seeded(){return seeded?1:0;}
}
