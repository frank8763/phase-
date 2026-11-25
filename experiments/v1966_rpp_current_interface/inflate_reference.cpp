// Independent brute nearest-lethal reference; same original Nav2 computeCost formula.
#include <cmath>
#include <iostream>
#include <vector>
int main(){int w,h;double res,inscribed,radius,scale;std::cin>>w>>h>>res>>inscribed>>radius>>scale;if(!std::cin||w<1||h<1||w*h>262144)return 2;std::vector<int>a(w*h);std::vector<int>lethal;for(int i=0;i<w*h;++i){std::cin>>a[i];if(a[i]==254)lethal.push_back(i);}int cap=std::ceil(radius/res);for(int i=0;i<w*h;++i){int best=cap*cap+1;for(auto j:lethal){int dx=i%w-j%w,dy=i/w-j/w;best=std::min(best,dx*dx+dy*dy);}int v=a[i];if(best<=cap*cap){double dist=std::sqrt(double(best));int c=dist==0?254:dist*res<=inscribed?253:static_cast<unsigned char>(252*std::exp(-scale*(dist*res-inscribed)));if(v!=255||c>=253)v=std::max(v==255?0:v,c);}std::cout<<v<<' ';}return 0;}
