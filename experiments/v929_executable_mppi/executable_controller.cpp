// Copyright (c) 2022 Samsung Research America, @artofnothingness Alexey Budyakov
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <stdint.h>
#include <chrono>
#include <sstream>
#include "std_msgs/msg/string.hpp"
#include "nav2_costmap_2d/footprint_collision_checker.hpp"
#include "executable_controller.hpp"
#include "nav2_mppi_controller/tools/utils.hpp"

// #define BENCHMARK_TESTING

namespace phase_predictive
{

void ExecutableMPPI::configure(
  const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
  std::string name, const std::shared_ptr<tf2_ros::Buffer> tf,
  const std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros)
{
  parent_ = parent;
  costmap_ros_ = costmap_ros;
  tf_buffer_ = tf;
  name_ = name;
  parameters_handler_ = std::make_unique<ParametersHandler>(parent);

  auto node = parent_.lock();
  diagnostics_=node->create_publisher<std_msgs::msg::String>("phase_mppi_diagnostics",10);
  // Get high-level controller parameters
  auto getParam = parameters_handler_->getParamGetter(name_);
  getParam(visualize_, "visualize", false);

  // Configure composed objects
  optimizer_.initialize(parent_, name_, costmap_ros_, parameters_handler_.get());
  path_handler_.initialize(parent_, name_, costmap_ros_, tf_buffer_, parameters_handler_.get());
  trajectory_visualizer_.on_configure(
    parent_, name_,
    costmap_ros_->getGlobalFrameID(), parameters_handler_.get());

  RCLCPP_INFO(logger_, "Configured executable-sample MPPI Controller: %s", name_.c_str());
}

void ExecutableMPPI::cleanup()
{
  optimizer_.shutdown();
  trajectory_visualizer_.on_cleanup();
  parameters_handler_.reset();
  RCLCPP_INFO(logger_, "Cleaned up MPPI Controller: %s", name_.c_str());
}

void ExecutableMPPI::activate()
{
  trajectory_visualizer_.on_activate();
  parameters_handler_->start();
  RCLCPP_INFO(logger_, "Activated MPPI Controller: %s", name_.c_str());
}

void ExecutableMPPI::deactivate()
{
  trajectory_visualizer_.on_deactivate();
  RCLCPP_INFO(logger_, "Deactivated MPPI Controller: %s", name_.c_str());
}

void ExecutableMPPI::reset()
{
  optimizer_.reset(false /*Don't reset zone-based speed limits between requests*/);
}

geometry_msgs::msg::TwistStamped ExecutableMPPI::computeVelocityCommands(
  const geometry_msgs::msg::PoseStamped & robot_pose,
  const geometry_msgs::msg::Twist & robot_speed,
  nav2_core::GoalChecker * goal_checker)
{
#ifdef BENCHMARK_TESTING
  auto start = std::chrono::system_clock::now();
#endif

  const auto computation_start=std::chrono::steady_clock::now();
  std::lock_guard<std::mutex> param_lock(*parameters_handler_->getLock());
  geometry_msgs::msg::Pose goal = path_handler_.getTransformedGoal(robot_pose.header.stamp).pose;

  nav_msgs::msg::Path transformed_plan = path_handler_.transformPath(robot_pose);

  nav2_costmap_2d::Costmap2D * costmap = costmap_ros_->getCostmap();
  std::unique_lock<nav2_costmap_2d::Costmap2D::mutex_t> costmap_lock(*(costmap->getMutex()));

  geometry_msgs::msg::TwistStamped cmd =
    optimizer_.evalControl(robot_pose, robot_speed, transformed_plan, goal, goal_checker);

  const auto &trajectory=optimizer_.validated();
  nav2_costmap_2d::FootprintCollisionChecker<nav2_costmap_2d::Costmap2D*>collision(costmap);
  const auto footprint=costmap_ros_->getRobotFootprint();
  for(unsigned i=0;i<trajectory.shape(0);++i){
    const double value=collision.footprintCostAtPose(trajectory(i,0),trajectory(i,1),trajectory(i,2),footprint);
    if(!std::isfinite(value)||value<0||value>=254)throw nav2_core::NoValidControl("EXECUTABLE_FILTERED_TRAJECTORY_COLLISION");
  }
  if(!std::isfinite(cmd.twist.linear.x)||!std::isfinite(cmd.twist.angular.z)||std::abs(cmd.twist.angular.z)>std::abs(cmd.twist.linear.x)*K+1e-6)
    throw nav2_core::NoValidControl("EXECUTABLE_OUTPUT_CONTRACT");

#ifdef BENCHMARK_TESTING
  auto end = std::chrono::system_clock::now();
  auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
  RCLCPP_INFO(logger_, "Control loop execution time: %ld [ms]", duration);
#endif

  if (visualize_) {
    visualize(std::move(transformed_plan), cmd.header.stamp);
  }

  std_msgs::msg::String record;
  std::ostringstream stream;stream.precision(17);
  stream<<"{\"gear\":"<<optimizer_.gear()<<",\"projected_samples\":"<<optimizer_.projected()
   <<",\"v\":"<<cmd.twist.linear.x<<",\"w\":"<<cmd.twist.angular.z
   <<",\"compute_s\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-computation_start).count()
   <<",\"final_full_trajectory_collision_checked\":true,\"samples\":"<<trajectory.shape(0)<<"}";
  record.data=stream.str();diagnostics_->publish(record);
  return cmd;
}

void ExecutableMPPI::visualize(
  nav_msgs::msg::Path transformed_plan,
  const builtin_interfaces::msg::Time & cmd_stamp)
{
  trajectory_visualizer_.add(optimizer_.getGeneratedTrajectories(), "Candidate Trajectories");
  trajectory_visualizer_.add(optimizer_.getOptimizedTrajectory(), "Optimal Trajectory", cmd_stamp);
  trajectory_visualizer_.visualize(std::move(transformed_plan));
}

void ExecutableMPPI::setPlan(const nav_msgs::msg::Path & path)
{
  path_handler_.setPath(path);
}

void ExecutableMPPI::setSpeedLimit(const double & speed_limit, const bool & percentage)
{
  optimizer_.setSpeedLimit(speed_limit, percentage);
}

}  // namespace phase_predictive

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(phase_predictive::ExecutableMPPI, nav2_core::Controller)
