#include <xtensor/xrandom.hpp>
#include <array>
#include <cstring>
#include <iostream>
int main(){
 std::array<float,56000>a{},b{},c{};
 auto draw=[](auto& out,unsigned long seed){
  xt::random::seed(seed);std::normal_distribution<float> normal(0.f,1.f);
  for(auto&v:out)v=normal(xt::random::get_default_random_engine());
 };
 draw(a,1234567);draw(b,1234567);draw(c,1234568);
 if(std::memcmp(a.data(),b.data(),sizeof(a))||!std::memcmp(a.data(),c.data(),sizeof(a)))return 1;
 std::cout<<"{\"passed\":true,\"same_seed_float_bytes_exact\":true,\"different_seed_distinct\":true,\"draws_each\":56000,\"optimizer_calls\":0,\"models\":0,\"physical_steps\":0}\n";
}
