#include <chrono>
#include <fstream>
#include <iostream>

#include "../include/manager.hpp"
#include "../include/router.hpp"

int main() {
  Manager manager;
  Router r1(1, &manager, {{2, 1000}});
  Router r2(2, &manager, {{1, 1000}, {3, 1000}});
  Router r3(3, &manager, {{2, 1000}});

  r1.set_forwarding_tables({{2, 2}, {3, 2}});
  r2.set_forwarding_tables({{1, 1}, {3, 3}});
  r3.set_forwarding_tables({{1, 2}, {2, 2}});

  manager.routers.push_back(r1);
  manager.routers.push_back(r2);
  manager.routers.push_back(r3);

  // messages
  manager.add_message(3, 1);
  manager.add_message(1, 3);

  // wait until all messages are recieved
  while (!manager.finished()) {
    manager.tick();
  }

  return 0;
}
