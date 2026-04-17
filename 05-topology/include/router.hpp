#ifndef _ROUTER_H_
#define _ROUTER_H_

#include <chrono>
#include <queue>
#include <unordered_map>

// Forward declare Manager
class Manager;

using namespace std::chrono;
template <class Duration>
using sys_time = time_point<system_clock, Duration>;

class Router {
 private:
  sys_time<milliseconds> last_sent;
  std::pair<int, int> next_msg;
  Manager* manager;

 public:
  int router_id;
  std::queue<int> message_queue;
  std::unordered_map<int, int> forwarding_table;
  std::unordered_map<int, milliseconds> delays;
  bool message_queued;

  Router(int, Manager*, std::unordered_map<int, int>);
  void set_forwarding_tables(std::unordered_map<int, int>);
  void add_message(int);
  void tick();
};

#endif /* _ROUTER_H_ */