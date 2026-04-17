#include <iostream>

#include "../include/manager.hpp"
#include "../include/router.hpp"
using namespace std::chrono;

Router::Router(int _router_id,
               Manager* _manager,
               std::unordered_map<int, int> _delays)
    : router_id(_router_id), manager(_manager), message_queued(false) {
  for (const auto& pair : _delays) {
    delays[pair.first] = milliseconds(pair.second);
  }
  last_sent = time_point_cast<milliseconds>(system_clock::now());
}

void Router::set_forwarding_tables(
    std::unordered_map<int, int> _forwarding_table) {
  forwarding_table = _forwarding_table;
}

void Router::add_message(int destination) {
  message_queue.push(destination);
}

void Router::tick() {
  if (message_queue.empty() and !message_queued) {
    return;
  }

  auto now = time_point_cast<milliseconds>(system_clock::now());
  // Check that we can send a message
  if (now < last_sent) {
    return;
  }

  // Send currently queued message
  if (message_queued) {
    for (auto& router : manager->routers) {
      if (router.router_id == next_msg.first) {
        router.add_message(next_msg.second);
        break;
      }
    }

    std::cout << "FORWARD :: R" << router_id << " (R" << next_msg.first << ", R"
              << next_msg.second << ")" << std::endl;
    message_queued = false;
  }

  // Prepare the next message
  if (!message_queue.empty()) {
    auto destination = message_queue.front();
    message_queue.pop();

    // Message delivered (no more forwarding)
    if (destination == router_id) {
      std::cout << "RECIEVED:: R" << router_id << std::endl;
      return;
    }

    // Determine where next message will be forwarded
    auto next_hop = forwarding_table[destination];
    next_msg = {next_hop, destination};
    message_queued = true;

    // Update last sent (used to delay sending of next_msg)
    last_sent = now + milliseconds(delays[next_hop]);
  }
}