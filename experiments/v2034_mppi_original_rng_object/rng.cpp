// Bind the original engine object and its C++ ABI guard; no noise math changes.
#include <random>
#include <new>
#include <cstdint>
#include <dlfcn.h>
#include <cxxabi.h>
#ifndef PHASE_RNG_CORE
#define PHASE_RNG_CORE "/opt/ros/jazzy/lib/libmppi_controller.so"
#endif
namespace {bool seeded=false;unsigned long long chosen=0,address=0;int initialized=0;}
extern "C" {
int phase_mppi_rng_seed(unsigned long long seed){
 if(seeded||seed>UINT32_MAX)return -1;
 static_assert(sizeof(std::mt19937)==5000,"PINNED_MPPI_ENGINE_ABI_SIZE");
 void* core=dlopen(PHASE_RNG_CORE,RTLD_NOW|RTLD_NOLOAD);if(!core)return -2;
 auto* engine=static_cast<std::mt19937*>(dlsym(core,"_ZZN2xt6random25get_default_random_engineEvE2mt"));
 auto* guard=static_cast<__cxxabiv1::__guard*>(dlsym(core,"_ZGVZN2xt6random25get_default_random_engineEvE2mt"));
 if(!engine||!guard){dlclose(core);return -3;}
 if(__cxxabiv1::__cxa_guard_acquire(guard)){
  new(engine)std::mt19937();__cxxabiv1::__cxa_guard_release(guard);initialized=1;
 }
 engine->seed(static_cast<std::mt19937::result_type>(seed));seeded=true;chosen=seed;address=reinterpret_cast<unsigned long long>(engine);dlclose(core);return 0;
}
unsigned long long phase_mppi_rng_chosen_seed(){return chosen;}
unsigned long long phase_mppi_rng_engine_address(){return address;}
int phase_mppi_rng_seeded(){return seeded?1:0;}
int phase_mppi_rng_initialized_original_guard(){return initialized;}
}
