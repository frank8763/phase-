// Read-only diagnostic, pinned Nav2 1.3.13 CriticData and xtensor 0.25 ABI.
#include <xtensor/xtensor.hpp>
#include <dlfcn.h>
#include <vector>
#include <optional>
#include <memory>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <cstring>
struct PathView{xt::xtensor<float,1>x,y,yaws;};
struct TrajectoryView{xt::xtensor<float,2>x,y,yaws;};
struct CriticView {
  const void *state,*trajectories,*path,*goal;
  xt::xtensor<float,1> *costs;
  float *model_dt;
  bool fail_flag;
  void *goal_checker;
  std::shared_ptr<void> motion_model;
  std::optional<std::vector<bool>> path_pts_valid;
  std::optional<std::size_t> furthest;
};
static_assert(offsetof(CriticView,costs)==32);
using Score = void (*)(void *,void *);
static void trace_score(void *self,void *opaque,const char *symbol,const char *name) {
    static void *library=dlopen("/opt/ros/jazzy/lib/libmppi_critics.so",RTLD_NOW|RTLD_NOLOAD);
    if(!library) std::abort();
    auto original=reinterpret_cast<Score>(dlsym(library,symbol));
    auto *data=static_cast<CriticView*>(opaque);
    if(!original || data->costs->size()!=1000 || data->costs->dimension()!=1 || std::abs(*data->model_dt-.05f)>1e-6) {
      std::fprintf(stderr,"[DEBUG-1314] INVALID_VIEW\n");std::abort();
    }
    std::vector<float> before(data->costs->begin(),data->costs->end());
    original(self,opaque);
    double sum=0.,square=0.,low=1e100,high=-1e100;
    for(std::size_t i=0;i<1000;++i) {
      double delta=(*data->costs)(i)-before[i];
      if(!std::isfinite(delta))std::abort();
      sum+=delta;square+=delta*delta;low=std::min(low,delta);high=std::max(high,delta);
    }
    auto furthest=data->furthest.value_or(0);
    if (std::strcmp(name,"Angle")==0) {
      auto *path=static_cast<const PathView*>(data->path);
      auto *traj=static_cast<const TrajectoryView*>(data->trajectories);
      if(path->x.size()<2 || path->x.size()>1000 || traj->x.shape(0)!=1000 || traj->x.shape(1)!=56)std::abort();
      auto index=std::min(furthest+4,path->x.size()-1);
      double gx=path->x(index),gy=path->y(index),ga=path->yaws(index),forward=0.,feasible=0.;std::size_t flipped=0;
      for(std::size_t i=0;i<1000;++i){
        double a=std::atan2(gy-traj->y(i,55),gx-traj->x(i,55));
        double error=std::atan2(std::sin(a-ga),std::cos(a-ga));
        double f=std::atan2(std::sin(a-traj->yaws(i,55)),std::cos(a-traj->yaws(i,55)));forward+=std::abs(f);
        if(std::abs(error)>=M_PI/2){++flipped;a=std::atan2(std::sin(a+M_PI),std::cos(a+M_PI));}
        feasible+=std::abs(std::atan2(std::sin(a-traj->yaws(i,55)),std::cos(a-traj->yaws(i,55))));
      }
      std::fprintf(stderr,"[DEBUG-1316] {\"flipped\":%zu,\"samples\":1000,\"mean_forward_angle\":%.17g,\"mean_mode2_angle\":%.17g,\"goal_x\":%.17g,\"goal_y\":%.17g,\"goal_yaw\":%.17g,\"path_index\":%zu}\n",flipped,forward/1000.,feasible/1000.,gx,gy,ga,index);
    }

    std::fprintf(stderr,"[DEBUG-1314] {\"critic\":\"%s\",\"mean\":%.17g,\"sd\":%.17g,\"minimum\":%.17g,\"maximum\":%.17g,\"furthest\":%zu}\n",name,sum/1000.,std::sqrt(std::max(0.,square/1000.-sum*sum/1000000.)),low,high,furthest);
    std::fflush(stderr);
}
#define HOOK(label,symbol) \
extern "C" void hook_##label(void*,void*) asm(symbol); \
extern "C" void hook_##label(void *self,void *data){trace_score(self,data,symbol,#label);}
HOOK(Constraint,"_ZN4mppi7critics16ConstraintCritic5scoreERNS_10CriticDataE")
HOOK(Cost,"_ZN4mppi7critics10CostCritic5scoreERNS_10CriticDataE")
HOOK(Goal,"_ZN4mppi7critics10GoalCritic5scoreERNS_10CriticDataE")
HOOK(GoalAngle,"_ZN4mppi7critics15GoalAngleCritic5scoreERNS_10CriticDataE")
HOOK(Align,"_ZN4mppi7critics15PathAlignCritic5scoreERNS_10CriticDataE")
HOOK(Follow,"_ZN4mppi7critics16PathFollowCritic5scoreERNS_10CriticDataE")
HOOK(Angle,"_ZN4mppi7critics15PathAngleCritic5scoreERNS_10CriticDataE")
HOOK(Forward,"_ZN4mppi7critics19PreferForwardCritic5scoreERNS_10CriticDataE")
