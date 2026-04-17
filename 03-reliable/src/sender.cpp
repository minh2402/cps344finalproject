#include "sender.hpp"
#include <chrono>
#include <cstring>
#include <iostream>
using asio::ip::tcp;

Sender::Sender(asio::io_context& io_context,
               std::string ip_addr,
               std::string port)
    : socket(io_context), num_msgs(0), finished(false) {
  tcp::resolver resolver(io_context);
  tcp::resolver::results_type endpoints = resolver.resolve(ip_addr, port);
  asio::connect(socket, endpoints);

  _t = std::thread([&] {
    while (true) {
      while (!socket.available()) {
        if (finished) {
          goto exit_thread;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(1));
      }

      asio::error_code error;
      std::array<char, CHUNK_SIZE + 2> buf;
      buf.fill(' ');
      asio::read(socket, asio::buffer(buf), error);
      if (error) {
        goto exit_thread;
      }

      std::lock_guard<std::mutex> lock(data_lock);
      if (num_msgs < data.size()) {
        uint16_t msg_id = 0;
        std::memcpy(&msg_id, buf.data(), sizeof(uint16_t));
        data[num_msgs].msg_id = msg_id;
        std::memcpy(data[num_msgs].data.data(), buf.data() + sizeof(uint16_t),
                    CHUNK_SIZE);
        num_msgs++;
      }
    }
  exit_thread:;
  });
}

Sender::~Sender() {
  finished = true;
  _t.join();
}

bool Sender::data_ready() {
  std::lock_guard<std::mutex> lock(data_lock);
  return num_msgs > 0;
}

Msg Sender::get_msg() {
  std::lock_guard<std::mutex> lock(data_lock);
  if (num_msgs == 0) {
    std::cout << "Warning: no Msg instance available! Aborting." << std::endl;
    exit(1);
  }

  auto msg = data[0];
  for (size_t i = 1; i < num_msgs; i++) {
    data[i - 1] = data[i];
  }
  num_msgs--;
  return msg;
}

void Sender::request_msg(uint16_t msg_id) {
  asio::error_code error;
  std::array<uint16_t, 1> msg_id_buf;
  msg_id_buf[0] = msg_id;
  asio::write(socket, asio::buffer(msg_id_buf), error);
}
