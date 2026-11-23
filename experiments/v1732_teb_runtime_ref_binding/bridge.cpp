// Thin C boundary only. Author planning bodies remain in the pinned library.
#include <teb_local_planner/homotopy_class_planner.h>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <memory>

extern "C" {
struct PhaseTebConfig {
  uint32_t abi, vertices;
  double forward, backward, omega, acceleration, angular_acceleration;
  double wheelbase, min_turning_radius, obstacle_distance;
  double footprint[32];
};
struct PhaseTebObstacle { double x,y,vx,vy; uint32_t dynamic; };
struct PhaseTebQuery {
  double x,y,yaw,goal_x,goal_y,goal_yaw,vx,vy,omega;
  uint32_t obstacles;
  const PhaseTebObstacle* data;
};
struct PhaseTebSample { double x,y,yaw,time,vx,vy,omega; };
struct PhaseTebResult { int32_t status; uint32_t samples,classes; double vx,vy,omega; uint64_t sequence; };
}
namespace {
std::atomic<uint64_t> created{0},planned{0},destroyed{0};
thread_local char message[512] = {};
struct Instance {
  teb_local_planner::TebConfig config;
  teb_local_planner::ObstContainer obstacles;
  std::unique_ptr<teb_local_planner::HomotopyClassPlanner> planner;
  uint64_t sequence=0;
};
void error(const char* value) { std::snprintf(message,sizeof(message),"%s",value); }
bool valid_number(double value) { return std::isfinite(value); }
}
extern "C" uint64_t phase_teb_meta(uint32_t key) noexcept {
  switch(key) {
    case 0:return 1; case 1:return sizeof(PhaseTebConfig); case 2:return sizeof(PhaseTebQuery);
    case 3:return sizeof(PhaseTebResult); case 4:return sizeof(PhaseTebSample); case 5:return sizeof(PhaseTebObstacle);
    case 6:return offsetof(PhaseTebConfig,footprint); case 7:return offsetof(PhaseTebQuery,data);
    case 8:return offsetof(PhaseTebResult,sequence); case 20:return created.load();
    case 21:return planned.load(); case 22:return destroyed.load(); default:return UINT64_MAX;
  }
}
extern "C" const char* phase_teb_error() noexcept { return message; }
extern "C" void* phase_teb_create(const PhaseTebConfig* c) noexcept {
  try {
    if(!c || c->abi!=1 || c->vertices<3 || c->vertices>16) { error("CONFIG_SCHEMA");return nullptr; }
    const double values[]={c->forward,c->backward,c->omega,c->acceleration,c->angular_acceleration,c->wheelbase,c->min_turning_radius,c->obstacle_distance};
    for(double value:values)if(!valid_number(value)||value<=0) {error("CONFIG_DOMAIN");return nullptr;}
    for(uint32_t i=0;i<c->vertices*2;i++)if(!valid_number(c->footprint[i])){error("FOOTPRINT_DOMAIN");return nullptr;}
    std::unique_ptr<Instance> p(new Instance);
    p->config.robot.max_vel_x=c->forward;p->config.robot.max_vel_x_backwards=c->backward;
    p->config.robot.max_vel_theta=c->omega;p->config.robot.acc_lim_x=c->acceleration;p->config.robot.acc_lim_theta=c->angular_acceleration;
    p->config.robot.wheelbase=c->wheelbase;p->config.robot.min_turning_radius=c->min_turning_radius;
    p->config.obstacles.min_obstacle_dist=c->obstacle_distance;
    // Original HCP selection is retained; only execution parallelism is disabled.
    p->config.hcp.enable_homotopy_class_planning=true;p->config.hcp.enable_multithreading=false;
    teb_local_planner::Point2dContainer polygon;
    for(uint32_t i=0;i<c->vertices;i++)polygon.emplace_back(c->footprint[i*2],c->footprint[i*2+1]);
    p->config.robot_model=boost::make_shared<teb_local_planner::PolygonRobotFootprint>(polygon);
    p->planner.reset(new teb_local_planner::HomotopyClassPlanner(p->config,&p->obstacles));
    created++;return p.release();
  }catch(const std::exception& e){error(e.what());return nullptr;}catch(...){error("CONSTRUCTOR_EXCEPTION");return nullptr;}
}
extern "C" int32_t phase_teb_plan(void* handle,const PhaseTebQuery* q,PhaseTebSample* samples,uint32_t capacity,PhaseTebResult* out) noexcept {
  try {
    if(!handle||!q||!out||!samples||capacity<500||q->obstacles>4096||(q->obstacles&&!q->data)){error("QUERY_SCHEMA");return -1;}
    const double values[]={q->x,q->y,q->yaw,q->goal_x,q->goal_y,q->goal_yaw,q->vx,q->vy,q->omega};
    for(double value:values)if(!valid_number(value)){error("QUERY_DOMAIN");return -1;}
    for(uint32_t i=0;i<q->obstacles;i++){const auto& a=q->data[i];if(!valid_number(a.x)||!valid_number(a.y)||!valid_number(a.vx)||!valid_number(a.vy)||a.dynamic>1){error("OBSTACLE_DOMAIN");return -1;}}
    auto& p=*static_cast<Instance*>(handle);p.obstacles.clear();
    for(uint32_t i=0;i<q->obstacles;i++){
      const auto& a=q->data[i];auto obstacle=boost::make_shared<teb_local_planner::PointObstacle>(a.x,a.y);
      if(a.dynamic)obstacle->setCentroidVelocity(Eigen::Vector2d(a.vx,a.vy));p.obstacles.push_back(obstacle);
    }
    geometry_msgs::Twist velocity;velocity.linear.x=q->vx;velocity.linear.y=q->vy;velocity.angular.z=q->omega;
    *out={};out->sequence=++p.sequence;planned++;
    bool accepted=p.planner->plan(teb_local_planner::PoseSE2(q->x,q->y,q->yaw),teb_local_planner::PoseSE2(q->goal_x,q->goal_y,q->goal_yaw),&velocity,false);
    auto best=p.planner->bestTeb();out->classes=p.planner->getTrajectoryContainer().size();
    if(!accepted||!best||!best->isOptimized()){out->status=1;error("NO_OPTIMIZED_SELECTED_TEB");return 1;}
    if(p.config.recovery.divergence_detection_enable&&p.planner->hasDiverged()){out->status=2;error("AUTHOR_DIVERGENCE_REFUSAL");return 2;}
    if(!p.planner->getVelocityCommand(out->vx,out->vy,out->omega,p.config.trajectory.control_look_ahead_poses)){out->status=3;error("AUTHOR_VELOCITY_REFUSAL");return 3;}
    std::vector<teb_local_planner::TrajectoryPointMsg> trajectory;best->getFullTrajectory(trajectory);
    if(trajectory.size()>capacity){error("OUTPUT_CAPACITY");return -1;}
    for(size_t i=0;i<trajectory.size();i++){
      const auto& a=trajectory[i];const auto& v=a.pose.orientation;
      samples[i]={a.pose.position.x,a.pose.position.y,std::atan2(2*(v.w*v.z+v.x*v.y),1-2*(v.y*v.y+v.z*v.z)),a.time_from_start.toSec(),a.velocity.linear.x,a.velocity.linear.y,a.velocity.angular.z};
    }
    out->samples=trajectory.size();out->status=0;return 0;
  }catch(const std::exception& e){error(e.what());return -2;}catch(...){error("PLAN_EXCEPTION");return -2;}
}
extern "C" void phase_teb_destroy(void* handle) noexcept { if(handle){delete static_cast<Instance*>(handle);destroyed++;} }
