// C boundary only. All sampling, cost and prediction math stays in author core.
#include <cmath>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>
#include "mppi_controller/stein_variational_guided_mppi.hpp"

namespace {
thread_local std::string error;
struct Handle {
    std::unique_ptr<mppi::cpu::SVGuidedMPPI> solver;
    int horizon;
    bool maps_ready = false;
    bool solve_failed = false;
    unsigned long long solve_attempts = 0, solve_returns = 0;
};
void require(bool value,const char* message) { if (!value) throw std::runtime_error(message); }
void finite(const double* data,int count) {
    require(data!=nullptr,"NULL_NUMERIC_BUFFER");
    for(int i=0;i<count;++i) require(std::isfinite(data[i]),"NONFINITE_NUMERIC_INPUT");
}
}

extern "C" {
int phase_svg_abi_version() { return 1; }
int phase_svg_state_dimension() { return mppi::STATE_SPACE::dim; }
int phase_svg_control_dimension() { return mppi::CONTROL_SPACE::dim; }
int phase_svg_error(char* output,int size) {
    if(!output||size<=0) return -1;
    const int n=std::min(size-1,static_cast<int>(error.size()));
    std::memcpy(output,error.data(),n);output[n]=0;return n;
}

// p[25]: explicit host-frozen vehicle, cost and author optimizer parameters.
// k[7]: horizon,samples,guides,gradient_samples,SVGD_iterations,nominal,covariance.
void* phase_svg_create(const double* p,int np,const int* k,int nk) {
    error.clear();
    try {
        require(np==25&&nk==7&&k,"CONFIGURATION_SHAPE");finite(p,np);
        require(k[0]>=2&&k[0]<=1000&&k[1]>=1&&k[1]<=10000,"HORIZON_OR_SAMPLE_CAP");
        require(k[2]>=1&&k[2]<=k[1]&&k[3]>=1&&k[3]<=1000&&k[4]>=1&&k[4]<=100,"GUIDE_GRADIENT_CAP");
        require((k[5]==0||k[5]==1)&&(k[6]==0||k[6]==1),"BOOLEAN_CONFIGURATION");
        require(p[0]>0&&p[2]>p[3]&&p[6]>0&&p[7]>0&&p[8]>=0&&p[9]>0,"VEHICLE_CONFIGURATION");
        require(p[15]>0&&p[16]>=0&&p[16]<=1&&p[17]>=0&&p[17]<=1&&p[18]>0,"SAMPLING_CONFIGURATION");
        require(p[19]>0&&p[20]>0&&p[21]>0&&p[22]>0&&p[23]>0&&p[24]>=p[23],"SVGD_CONFIGURATION");
        mppi::Params::Common a{};
        a.thread_num=1;a.prediction_step_size=k[0];a.prediction_interval=p[0];a.reference_speed=p[1];
        a.max_steer_angle=p[2];a.min_steer_angle=p[3];a.max_accel=p[4];a.min_accel=p[5];a.lr=p[6];a.lf=p[7];
        a.steer_delay=p[8];a.steer_1st_delay=p[9];a.q_dist=p[10];a.q_angle=p[11];a.collision_weight=p[12];
        a.q_terminal_dist=p[13];a.q_terminal_angle=p[14];a.is_localize_less_mode=false;a.speed_prediction_mode="reference";
        mppi::Params::SVGuidedMPPI b{};
        b.sample_batch_num=k[1];b.guide_sample_num=k[2];b.sample_num_for_grad_estimation=k[3];b.num_svgd_iteration=k[4];
        b.is_use_nominal_solution=k[5];b.is_covariance_adaptation=k[6];b.lambda=p[15];b.alpha=p[16];
        b.non_biased_sampling_rate=p[17];b.steer_cov=p[18];b.grad_lambda=p[19];b.steer_cov_for_grad_estimation=p[20];
        b.svgd_step_size=p[21];b.gaussian_fitting_lambda=p[22];b.min_steer_cov=p[23];b.max_steer_cov=p[24];
        auto h=std::make_unique<Handle>();h->horizon=k[0];h->solver=std::make_unique<mppi::cpu::SVGuidedMPPI>(a,b);
        return h.release();
    } catch(const std::exception& e) {error=e.what();return nullptr;}
}

// Four planes, each explicitly row-major[x_index * ny + y_index], grid_map's
// native index orientation. No obstacle/actor values are fabricated here.
int phase_svg_set_maps(void* opaque,int nx,int ny,double resolution,double cx,double cy,
                       const double* collision,const double* distance,const double* angle,const double* speed) {
    error.clear();
    try {
        auto* h=static_cast<Handle*>(opaque);require(h&&!h->solve_failed,"HANDLE_NOT_READY");h->maps_ready=false;
        require(nx>0&&ny>0&&nx<=2048&&ny<=2048&&nx*ny<=1000000,"MAP_SHAPE_CAP");
        require(std::isfinite(resolution)&&resolution>0&&std::isfinite(cx)&&std::isfinite(cy),"MAP_GEOMETRY");
        finite(collision,nx*ny);finite(distance,nx*ny);finite(angle,nx*ny);finite(speed,nx*ny);
        grid_map::GridMap obstacles({"collision_layer"});
        grid_map::GridMap reference({"distance_field","angle_field","speed_field"});
        obstacles.setGeometry(grid_map::Length(nx*resolution,ny*resolution),resolution,grid_map::Position(cx,cy));
        reference.setGeometry(grid_map::Length(nx*resolution,ny*resolution),resolution,grid_map::Position(cx,cy));
        require(obstacles.getSize()(0)==nx&&obstacles.getSize()(1)==ny,"MAP_ROUNDING_MISMATCH");
        for(int x=0;x<nx;++x) for(int y=0;y<ny;++y) {
            const int i=x*ny+y;
            obstacles["collision_layer"](x,y)=collision[i];reference["distance_field"](x,y)=distance[i];
            reference["angle_field"](x,y)=angle[i];reference["speed_field"](x,y)=speed[i];
        }
        h->solver->set_obstacle_map(obstacles);h->solver->set_reference_map(reference);h->maps_ready=true;return 0;
    } catch(const std::exception& e) {error=e.what();return -1;}
}

int phase_svg_solve(void* opaque,const double* state,int state_size,double* controls,int capacity,double* collision_rate) {
    error.clear();auto* h=static_cast<Handle*>(opaque);
    try {
        require(h&&h->maps_ready&&!h->solve_failed,"SOLVER_NOT_READY_OR_POISONED");
        require(state_size==5&&controls&&capacity==h->horizon-1&&collision_rate,"OUTPUT_BUFFER_SHAPE");finite(state,5);
        mppi::cpu::State initial;for(int i=0;i<5;++i) initial(i)=state[i];
        ++h->solve_attempts;h->solve_failed=true;
        auto answer=h->solver->solve(initial);
        require(answer.first.rows()==capacity&&answer.first.cols()==1,"AUTHOR_OUTPUT_SHAPE");
        require(answer.first.allFinite()&&std::isfinite(answer.second),"AUTHOR_OUTPUT_NONFINITE");
        for(int i=0;i<capacity;++i) controls[i]=answer.first(i,0);
        *collision_rate=answer.second;++h->solve_returns;h->solve_failed=false;return 0;
    } catch(const std::exception& e) {error=e.what();return -1;}
}
int phase_svg_call_counts(void* opaque,unsigned long long* values,int count) {
    auto* h=static_cast<Handle*>(opaque);if(!h||!values||count!=2)return -1;
    values[0]=h->solve_attempts;values[1]=h->solve_returns;return 0;
}
void phase_svg_destroy(void* opaque) {delete static_cast<Handle*>(opaque);}
}
