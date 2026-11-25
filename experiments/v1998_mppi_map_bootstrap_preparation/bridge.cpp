// Explicit synchronous C boundary around the already-disclosed ExecutableRPP.
// Neither upstream controller nor paired projection source is changed.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <limits>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "nav2_costmap_2d/costmap_2d_ros.hpp"
#include "tf2_ros/buffer.hpp"
#include "nav2_core/goal_checker.hpp"
#include "nav2_core/controller.hpp"
#include "pluginlib/class_loader.hpp"

namespace {
thread_local std::string error_text;
std::mutex api_mutex;
struct Goal final:nav2_core::GoalChecker{
 void initialize(const rclcpp_lifecycle::LifecycleNode::WeakPtr&,const std::string&,const std::shared_ptr<nav2_costmap_2d::Costmap2DROS>)override{}
 void reset()override{}
 bool isGoalReached(const geometry_msgs::msg::Pose&,const geometry_msgs::msg::Pose&,const geometry_msgs::msg::Twist&)override{return false;}
 bool getTolerances(geometry_msgs::msg::Pose&p,geometry_msgs::msg::Twist&v)override{
  p.position.x=p.position.y=.08;p.position.z=std::numeric_limits<double>::lowest();p.orientation.z=std::sin(M_PI/2.);p.orientation.w=std::cos(M_PI/2.);
  v.linear.x=v.linear.y=v.linear.z=v.angular.x=v.angular.y=v.angular.z=std::numeric_limits<double>::lowest();return true;
 }
};
struct Handle{
 std::shared_ptr<rclcpp_lifecycle::LifecycleNode>node;
 std::shared_ptr<nav2_costmap_2d::Costmap2DROS>map;
 std::shared_ptr<tf2_ros::Buffer>tf;
 std::unique_ptr<pluginlib::ClassLoader<nav2_core::Controller>>loader;
 std::shared_ptr<nav2_core::Controller>controller;
 std::vector<double> previous_path;Goal goal;unsigned long long calls=0;long long last_tick=-1;bool poisoned=false;
 Handle(){
  if(!rclcpp::ok()){int argc=0;char**argv=nullptr;rclcpp::init(argc,argv);}
  std::vector<rclcpp::Parameter>override_params;
#include "registered_parameters.inc"
  rclcpp::NodeOptions options;options.parameter_overrides(override_params);node=std::make_shared<rclcpp_lifecycle::LifecycleNode>("phase_mppi_sync",options);
  map=std::make_shared<nav2_costmap_2d::Costmap2DROS>("phase_mppi_sync_map");
  map->set_parameter(rclcpp::Parameter("global_frame",std::string("odom")));
  map->set_parameter(rclcpp::Parameter("robot_base_frame",std::string("base_link")));
  map->set_parameter(rclcpp::Parameter("plugins",std::vector<std::string>{}));
  map->set_parameter(rclcpp::Parameter("update_frequency",0.0));
  map->set_parameter(rclcpp::Parameter("width",int64_t(6)));
  map->set_parameter(rclcpp::Parameter("height",int64_t(6)));
  map->set_parameter(rclcpp::Parameter("resolution",0.05));
  map->set_parameter(rclcpp::Parameter("rolling_window",true));
  map->set_parameter(rclcpp::Parameter("footprint","[[-0.2907257858564467, -0.375], [-0.28782963214521234, -0.4044051420988682], [-0.2792524685744503, -0.4326802610774705], [-0.26532391073005623, -0.4587387599703287], [-0.2465792252787649, -0.48157922527876484], [-0.22373875997032877, -0.5003239107300562], [-0.1976802610774706, -0.5142524685744503], [-0.16940514209886826, -0.5228296321452123], [-0.14000000000000004, -0.5257257858564467], [0.74, -0.5257257858564467], [0.7694051420988681, -0.5228296321452124], [0.7976802610774706, -0.5142524685744503], [0.8237387599703287, -0.5003239107300562], [0.8465792252787648, -0.4815792252787649], [0.8653239107300562, -0.45873875997032876], [0.8792524685744503, -0.4326802610774706], [0.8878296321452123, -0.40440514209886824], [0.8907257858564467, -0.375], [0.8907257858564467, 0.375], [0.8878296321452124, 0.4044051420988682], [0.8792524685744503, 0.43268026107747054], [0.8653239107300562, 0.45873875997032876], [0.8465792252787648, 0.48157922527876484], [0.8237387599703287, 0.5003239107300562], [0.7976802610774705, 0.5142524685744503], [0.7694051420988681, 0.5228296321452124], [0.74, 0.5257257858564467], [-0.14, 0.5257257858564467], [-0.16940514209886817, 0.5228296321452124], [-0.19768026107747053, 0.5142524685744503], [-0.22373875997032872, 0.5003239107300562], [-0.24657922527876486, 0.48157922527876484], [-0.26532391073005623, 0.45873875997032876], [-0.2792524685744503, 0.43268026107747054], [-0.28782963214521234, 0.40440514209886824], [-0.2907257858564467, 0.375]]"));
  map->set_parameter(rclcpp::Parameter("footprint_padding",0.0));
  map->set_parameter(rclcpp::Parameter("transform_tolerance",0.15));
  if(map->on_configure(map->get_current_state())!=nav2_util::CallbackReturn::SUCCESS)throw std::runtime_error("MAP_CONFIGURE_REFUSED");
  tf=std::make_shared<tf2_ros::Buffer>(node->get_clock());loader=std::make_unique<pluginlib::ClassLoader<nav2_core::Controller>>("nav2_core","nav2_core::Controller");controller=loader->createSharedInstance("phase_deadband/DeadbandMPPI");controller->configure(node,"Deadband",tf,map);controller->activate();
 }
 ~Handle(){if(controller){controller->deactivate();controller->cleanup();}if(map)map->on_cleanup(map->get_current_state());}
};
bool finite(const double*p,size_t n){for(size_t i=0;i<n;++i)if(!std::isfinite(p[i]))return false;return true;}
}
extern "C" {
int phase_mppi_abi_version(){return 1;}
int phase_mppi_request_dimension(){return 5;}
int phase_mppi_error(char*out,int n){if(!out||n<1)return -1;std::strncpy(out,error_text.c_str(),n-1);out[n-1]=0;return static_cast<int>(error_text.size());}
void*phase_mppi_create(){std::lock_guard<std::mutex>guard(api_mutex);try{error_text.clear();return new Handle();}catch(const std::exception&e){error_text=e.what();return nullptr;}}
// Pose and path are both REAR-AXLE frame in odom, converted by qualified caller.
// Complete already-causally-built/inflated uint8 costmap is caller-owned data.
int phase_mppi_solve(void*raw,long long native_tick,const double*rear_pose_speed,
 const double*path_xyyaw,int poses,const unsigned char*grid,int width,int height,
 double resolution,double ox,double oy,const double*footprint_xy,int vertices,double*out){
 std::lock_guard<std::mutex>guard(api_mutex);auto*h=static_cast<Handle*>(raw);if(!h||!out)return -1;
 if(h->poisoned)return -2;h->poisoned=true;
 try{
  if(native_tick<=h->last_tick||!rear_pose_speed||!finite(rear_pose_speed,5)||!path_xyyaw||poses<2||poses>10000||!finite(path_xyyaw,poses*3)||!grid||width<1||height<1||width>512||height>512||!(resolution>0&&resolution<=.1)||!std::isfinite(ox)||!std::isfinite(oy)||!footprint_xy||vertices<4||vertices>128||!finite(footprint_xy,vertices*2))throw std::runtime_error("MPPI_C_INPUT_OR_ONCE_REFUSED");
  auto*costmap=h->map->getCostmap();{
   std::unique_lock<nav2_costmap_2d::Costmap2D::mutex_t>lock(*costmap->getMutex());costmap->resizeMap(width,height,resolution,ox,oy);std::memcpy(costmap->getCharMap(),grid,static_cast<size_t>(width)*height);
  }
  std::vector<geometry_msgs::msg::Point>footprint;for(int i=0;i<vertices;++i){geometry_msgs::msg::Point q;q.x=footprint_xy[2*i];q.y=footprint_xy[2*i+1];footprint.push_back(q);}h->map->setRobotFootprint(footprint);
  const auto stamp=h->node->now();geometry_msgs::msg::TransformStamped transform;transform.header.stamp=stamp;transform.header.frame_id="odom";transform.child_frame_id="base_link";transform.transform.translation.x=rear_pose_speed[0];transform.transform.translation.y=rear_pose_speed[1];transform.transform.rotation.z=std::sin(rear_pose_speed[2]/2);transform.transform.rotation.w=std::cos(rear_pose_speed[2]/2);if(!h->tf->setTransform(transform,"phase_current_receipt",false))throw std::runtime_error("MPPI_CURRENT_TF_REFUSED");
  nav_msgs::msg::Path plan;plan.header.frame_id="odom";plan.header.stamp=stamp;for(int i=0;i<poses;++i){geometry_msgs::msg::PoseStamped p;p.header=plan.header;p.pose.position.x=path_xyyaw[3*i];p.pose.position.y=path_xyyaw[3*i+1];p.pose.orientation.z=std::sin(path_xyyaw[3*i+2]/2);p.pose.orientation.w=std::cos(path_xyyaw[3*i+2]/2);plan.poses.push_back(p);}if(h->previous_path.size()!=static_cast<size_t>(poses*3)||std::memcmp(h->previous_path.data(),path_xyyaw,poses*3*sizeof(double))!=0){h->controller->setPlan(plan);h->previous_path.assign(path_xyyaw,path_xyyaw+poses*3);}
  geometry_msgs::msg::PoseStamped measured;measured.header=plan.header;measured.pose.position.x=rear_pose_speed[0];measured.pose.position.y=rear_pose_speed[1];measured.pose.orientation.z=std::sin(rear_pose_speed[2]/2);measured.pose.orientation.w=std::cos(rear_pose_speed[2]/2);geometry_msgs::msg::Twist velocity;velocity.linear.x=rear_pose_speed[3];velocity.angular.z=rear_pose_speed[4];++h->calls;auto command=h->controller->computeVelocityCommands(measured,velocity,&h->goal);
  if(!std::isfinite(command.twist.linear.x)||!std::isfinite(command.twist.angular.z))throw std::runtime_error("MPPI_NONFINITE_OUTPUT");out[0]=command.twist.linear.x;out[1]=command.twist.angular.z;h->last_tick=native_tick;h->poisoned=false;return 0;
 }catch(const std::exception&e){error_text=e.what();return -3;}
}
unsigned long long phase_mppi_call_count(void*raw){auto*h=static_cast<Handle*>(raw);return h?h->calls:0;}
int phase_mppi_poisoned(void*raw){auto*h=static_cast<Handle*>(raw);return !h||h->poisoned;}
void phase_mppi_destroy(void*raw){std::lock_guard<std::mutex>guard(api_mutex);delete static_cast<Handle*>(raw);}
}
