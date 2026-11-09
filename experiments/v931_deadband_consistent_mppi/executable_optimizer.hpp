// Derived from upstream Navigation2 1.3.13 (Apache-2.0). Keep optimizer/scorers.
#pragma once
#include "executable_projection.hpp"
#include "nav2_mppi_controller/optimizer.hpp"
#include "nav2_mppi_controller/tools/utils.hpp"
namespace phase_deadband {
class ExecutableModel: public mppi::AckermannMotionModel {
public:
 ExecutableModel(mppi::ParametersHandler *p,const std::string &name):AckermannMotionModel(p,name){}
 int gear{1};unsigned projected{0};
 void predict(mppi::models::State &state)override {
  mppi::MotionModel::predict(state);
  projected=project_samples(state,gear,control_constraints_.vx_min,control_constraints_.vx_max);
 }
};
class ExecutableOptimizer: public mppi::Optimizer {
 std::shared_ptr<ExecutableModel> model_;
 int gear_{0};
 xt::xtensor<float,2> validated_;
public:
 void initialize(rclcpp_lifecycle::LifecycleNode::WeakPtr parent,const std::string &name,std::shared_ptr<nav2_costmap_2d::Costmap2DROS>costmap,mppi::ParametersHandler *params){
  mppi::Optimizer::initialize(parent,name,costmap,params);
  model_=std::make_shared<ExecutableModel>(params,name);model_->initialize(settings_.constraints,settings_.model_dt);motion_model_=model_;
 }
 const xt::xtensor<float,2>& validated()const{return validated_;}
 int gear()const{return gear_;}unsigned projected()const{return model_->projected;}
 geometry_msgs::msg::TwistStamped evalControl(const geometry_msgs::msg::PoseStamped &pose,const geometry_msgs::msg::Twist &speed,const nav_msgs::msg::Path &path,const geometry_msgs::msg::Pose &goal,nav2_core::GoalChecker *checker){
  int requested=0;
  for(size_t i=0;i+1<path.poses.size();++i){
   auto&a=path.poses[i].pose;auto&b=path.poses[i+1].pose;double dx=b.position.x-a.position.x,dy=b.position.y-a.position.y;
   double yaw=tf2::getYaw(a.orientation);double forward=dx*std::cos(yaw)+dy*std::sin(yaw);
   if(std::hypot(dx,dy)>.002&&std::abs(forward)>.001){requested=forward>0?1:-1;break;}
  }
  if(requested==0)requested=gear_==0?1:gear_;
  if(gear_!=requested){reset(false);gear_=requested;}
  model_->gear=gear_;
  prepare(pose,speed,path,goal,checker);
  do{optimize();}while(fallback(critics_data_.fail_flag));
  mppi::utils::savitskyGolayFilter(control_sequence_,control_history_,settings_);
  applyControlSequenceConstraints();
  project_sequence(control_sequence_,gear_,settings_.constraints.vx_min,settings_.constraints.vx_max);
  const unsigned offset=settings_.shift_control_sequence?1:0;
  control_history_[3]={control_sequence_.vx(offset),control_sequence_.vy(offset),control_sequence_.wz(offset)};
  validated_=getOptimizedTrajectory();
  auto control=getControlFromSequenceAsTwist(path.header.stamp);last_command_vel_=control.twist;
  if(settings_.shift_control_sequence)shiftControlSequence();
  return control;
 }
};
}
