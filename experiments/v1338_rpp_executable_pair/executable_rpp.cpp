// Engineering adaptation of the installed, pinned upstream RPP. No safety theorem.
#include <cstdio>
#include <limits>
#include <mutex>
#include "nav2_regulated_pure_pursuit_controller/regulated_pure_pursuit_controller.hpp"
#include "nav2_core/controller_exceptions.hpp"
#include "pluginlib/class_list_macros.hpp"
#include "project_pair.hpp"

namespace phase_rpp {
class ExecutableRPP : public nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController {
 public:
  geometry_msgs::msg::TwistStamped computeVelocityCommands(
    const geometry_msgs::msg::PoseStamped &pose,const geometry_msgs::msg::Twist &speed,
    nav2_core::GoalChecker *goal) override {
    auto command=RegulatedPurePursuitController::computeVelocityCommands(pose,speed,goal);
    const double raw_v=command.twist.linear.x,raw_w=command.twist.angular.z;
    const auto executable=project(raw_v,raw_w);
    std::lock_guard<std::mutex> parameters(param_handler_->getMutex());
    std::unique_lock<nav2_costmap_2d::Costmap2D::mutex_t> map_lock(*(costmap_->getMutex()));
    // Recheck the sequence that would actually be sent, even when unchanged.
    // Infinite carrot distance retains the full existing1.5s configured horizon.
    if(collision_checker_->isCollisionImminent(pose,executable.v,executable.w,
                                             std::numeric_limits<double>::infinity()))
      throw nav2_core::NoValidControl("EXECUTABLE_RPP_PROJECTED_PAIR_COLLISION");
    command.twist.linear.x=executable.v;command.twist.angular.z=executable.w;
    std::fprintf(stderr,"[V1338_PAIR] {\"raw_v\":%.17g,\"raw_w\":%.17g,\"v\":%.17g,\"w\":%.17g,\"projected_pair_collision_rechecked\":true}\n",
                 raw_v,raw_w,executable.v,executable.w);
    std::fflush(stderr);
    return command;
  }
};
}
PLUGINLIB_EXPORT_CLASS(phase_rpp::ExecutableRPP,nav2_core::Controller)
