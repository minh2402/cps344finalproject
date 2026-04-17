#include <chrono>
#include <thread>

#include "../include/manager.hpp"
#include "../include/router.hpp"

void Manager::tick() {
  for (auto& router : routers) {
    router.tick();
  }
}

void Manager::add_message(int source, int destination) {
  for (auto& router : routers) {
    if (router.router_id == source) {
      router.add_message(destination);
      break;
    }
  }
  std::this_thread::sleep_for(std::chrono::milliseconds(1));
}

bool Manager::finished() {
  for (auto& router : routers) {
    if (!router.message_queue.empty() || router.message_queued) {
      return false;
    }
  }
  return true;
}