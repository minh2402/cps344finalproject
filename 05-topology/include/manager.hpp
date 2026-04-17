#ifndef _MANAGER_H_
#define _MANAGER_H_
#include <vector>
#include "../include/router.hpp"

class Manager {
 public:
  std::vector<Router> routers;
  void tick();
  void add_message(int, int);
  bool finished();
};

#endif /* _MANAGER_H_ */