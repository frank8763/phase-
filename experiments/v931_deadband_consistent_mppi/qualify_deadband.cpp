#include <iostream>
#include <random>
#include <limits>
#include "executable_projection.hpp"
#include "nav2_mppi_controller/models/state.hpp"
#include "nav2_mppi_controller/models/control_sequence.hpp"
#include "nav2_mppi_controller/tools/utils.hpp"
static bool executable(double v,double w){return std::isfinite(v)&&std::isfinite(w)&&std::abs(v)<=.100001&&std::abs(w)<=std::abs(v)/1.32+1e-6&&(!(std::abs(v)<.005)||std::abs(w)<=1e-6);}
int main(){
 mppi::models::ControlSequence q;q.reset(56);q.vx.fill(-.0009860588470473886f);q.wz.fill(-.0007470142445527017f);
 phase_deadband::project_sequence(q,-1,-.1f,.1f);
 if(!executable(q.vx(0),q.wz(0))||q.vx(0)!=0||q.wz(0)!=0){std::cerr<<"SAVED_GEAR_CHANGE_NOT_EXECUTABLE "<<q.vx(0)<<" "<<q.wz(0)<<std::endl;return 1;}
 unsigned checked=0;std::mt19937 rng(931);std::uniform_real_distribution<float>d(-.12f,.12f);
 mppi::models::State s;s.reset(1000,56);s.vx.fill(.03f);s.wz.fill(.02f);
 for(int gear:{1,-1})for(int trial=0;trial<10;++trial){
  for(float&v:s.cvx)v=d(rng);for(float&w:s.cwz)w=d(rng);
  phase_deadband::project_samples(s,gear,-.1f,.1f);
  for(unsigned i=0;i<1000;++i)for(unsigned j=0;j<56;++j){
   float v=s.cvx(i,j),w=s.cwz(i,j);if(!executable(v,w)||(std::abs(v)<.005&&(v!=0||w!=0)))return 2;
   if(j>0&&(s.vx(i,j)!=s.cvx(i,j-1)||s.wz(i,j)!=s.cwz(i,j-1)))return 3;++checked;
  }
  if(s.vx(0,0)!=.03f||s.wz(0,0)!=.02f)return 4;
 }
 float edge=.005f;float below=std::nextafter(edge,0.f),above=std::nextafter(edge,1.f);
 for(float v:{0.f,below,edge,above,-below,-edge,-above}){
  q.vx.fill(v);q.wz.fill(v*.5f);phase_deadband::project_sequence(q,v<0?-1:1,-.1f,.1f);
  if(!executable(q.vx(0),q.wz(0))||(std::abs(double(v))<.005&&(q.vx(0)!=0||q.wz(0)!=0)))return 5;
 }
 unsigned smoothed=0;
 for(int gear:{1,-1})for(int trial=0;trial<20;++trial){
  q.reset(56);q.vx.fill(0.f);q.wz.fill(0.f);q.vx(0)=gear*.0051f;q.vx(1)=gear*.0051f;q.wz(0)=.002f;q.wz(1)=.002f;
  std::array<mppi::models::Control,4>history{};mppi::models::OptimizerSettings settings;settings.shift_control_sequence=true;
  mppi::utils::savitskyGolayFilter(q,history,settings);
  phase_deadband::project_sequence(q,gear,-.1f,.1f);
  for(unsigned j=0;j<56;++j){if(!executable(q.vx(j),q.wz(j)))return 6;++smoothed;}
 }
 std::cout<<"{\"passed\":true,\"models\":0,\"integrations\":0,\"saved_gear_change_regressed\":true,\"sample_controls_checked\":"<<checked<<",\"float_deadband_boundaries_checked\":7,\"upstream_sg_outputs_checked\":"<<smoothed<<",\"prediction_and_controls_same\":true,\"measured_initial_state_kept\":true}"<<std::endl;
}
