#include <iostream>
#include <random>
#include <limits>
#include "executable_projection.hpp"
#include "nav2_mppi_controller/motion_models.hpp"
int main(){
 mppi::models::ControlConstraints limits{.1f,-.1f,0.f,.076f,.4f,-.4f,0.f,0.f,.4f};
 mppi::DiffDriveMotionModel original;original.initialize(limits,.05f);
 mppi::models::State s;s.reset(1000,56);s.speed.linear.x=.03;
 s.vx.fill(.03f);s.wz.fill(.02f);s.cvx.fill(.03f);s.cwz.fill(.2f);
 original.predict(s);
 unsigned infeasible=0;for(unsigned i=0;i<1000;++i)for(unsigned j=1;j<56;++j)infeasible+=std::abs(s.wz(i,j))>std::abs(s.vx(i,j))*phase_deadband::K+1e-6f;
 if(infeasible==0)throw std::runtime_error("DID_NOT_REPRODUCE_OLD_SAMPLE_FEASIBILITY_GAP");
 auto changed=phase_deadband::project_samples(s,1,-.1f,.1f);
 unsigned violations=0;for(unsigned i=0;i<1000;++i)for(unsigned j=1;j<56;++j)violations+=std::abs(s.wz(i,j))>std::abs(s.vx(i,j))*phase_deadband::K+1e-6f;
 if(violations||s.vx(0,0)!=.03f||s.wz(0,0)!=.02f)throw std::runtime_error("NEW_SAMPLES_OR_MEASURED_STATE_CHANGED");
 std::mt19937 rng(929);std::uniform_real_distribution<float>dist(-.4f,.4f);unsigned tested=0;
 for(int gear:{1,-1})for(int trial=0;trial<10;++trial){
  for(auto &x:s.cvx)x=dist(rng);for(auto &x:s.cwz)x=dist(rng);
  phase_deadband::project_samples(s,gear,-.1f,.1f);
  for(unsigned i=0;i<1000;++i)for(unsigned j=0;j<56;++j){float v=s.cvx(i,j),w=s.cwz(i,j);if(v*gear<0||std::abs(v)>.100001||std::abs(w)>std::abs(v)*phase_deadband::K+1e-6)throw std::runtime_error("CONSTRAINT_VIOLATION");++tested;}
 }
 bool nan=false,badgear=false;
 try{s.cwz(0,0)=std::numeric_limits<float>::quiet_NaN();phase_deadband::project_samples(s,1,-.1,.1);}catch(const std::runtime_error&){nan=true;}
 try{phase_deadband::projected_v(.1,0,-.1,.1);}catch(const std::runtime_error&){badgear=true;}
 if(!nan||!badgear)throw std::runtime_error("NEGATIVE_NOT_REJECTED");
 std::cout<<"{\"passed\":true,\"models\":0,\"old_infeasible_sample_states\":"<<infeasible<<",\"new_infeasible_sample_states\":"<<violations<<",\"changed_old_samples\":"<<changed<<",\"random_sample_controls_checked\":"<<tested<<",\"measured_initial_state_kept\":true,\"nan_rejected\":true,\"invalid_gear_rejected\":true}"<<std::endl;
}
