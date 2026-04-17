#include "../include/sender.hpp"
#include <asio.hpp>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

using asio::ip::tcp;

int main() {
  constexpr uint16_t WINDOW_SIZE = 10;
  const std::chrono::milliseconds RETRANSMIT_TIMEOUT(700);
  const std::string output_path = "../data/output.txt";

  asio::io_context io_context;
  Sender sender(io_context, "127.0.0.1", "3000");

  std::ofstream outfile(output_path, std::ios::binary | std::ios::trunc);
  if (!outfile.is_open()) {
    std::cerr << "Unable to open output file: " << output_path << std::endl;
    return 1;
  }

  std::vector<bool> requested(NUM_MSGS, false);
  std::vector<bool> received(NUM_MSGS, false);
  std::vector<std::string> chunks(NUM_MSGS);
  std::vector<std::chrono::steady_clock::time_point> last_request(NUM_MSGS);

  uint16_t next_expected = 0;
  size_t total_written = 0;

  while (total_written < NUM_MSGS) {
    const auto now = std::chrono::steady_clock::now();
    uint16_t window_end = next_expected + WINDOW_SIZE;
    if (window_end > NUM_MSGS) {
      window_end = NUM_MSGS;
    }

    for (uint16_t msg_id = next_expected; msg_id < window_end; ++msg_id) {
      if (!requested[msg_id]) {
        sender.request_msg(msg_id);
        requested[msg_id] = true;
        last_request[msg_id] = now;
      } else if (!received[msg_id] &&
                 now - last_request[msg_id] >= RETRANSMIT_TIMEOUT) {
        sender.request_msg(msg_id);
        last_request[msg_id] = now;
      }
    }

    bool made_progress = false;
    while (sender.data_ready()) {
      Msg msg = sender.get_msg();
      uint16_t msg_id = msg.msg_id;
      if (msg_id >= NUM_MSGS) {
        continue;
      }

      if (received[msg_id]) {
        continue;
      }

      chunks[msg_id] = std::string(msg.data.data(), CHUNK_SIZE);
      received[msg_id] = true;
      made_progress = true;
    }

    while (next_expected < NUM_MSGS && received[next_expected]) {
      outfile.write(chunks[next_expected].data(), CHUNK_SIZE);
      ++next_expected;
      ++total_written;
      made_progress = true;
    }

    if (!made_progress) {
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
  }

  outfile.flush();
  std::cout << "Reconstructed file written to " << output_path << std::endl;
  return 0;
}
