// Software-only ABI fixture, not an algorithm or plant library.
#include <random>
#include <new>
#include <cxxabi.h>
alignas(std::mt19937) unsigned char engine_bytes[sizeof(std::mt19937)] asm("_ZZN2xt6random25get_default_random_engineEvE2mt")={};
__cxxabiv1::__guard engine_guard asm("_ZGVZN2xt6random25get_default_random_engineEvE2mt")=0;
extern "C" void fixture_initialize(){
 if(__cxxabiv1::__cxa_guard_acquire(&engine_guard)){
  new(engine_bytes)std::mt19937();__cxxabiv1::__cxa_guard_release(&engine_guard);
 }
}
extern "C" unsigned long fixture_draw(){fixture_initialize();return (*reinterpret_cast<std::mt19937*>(engine_bytes))();}
