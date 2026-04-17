cmake_minimum_required(VERSION 3.1)
project(sockets)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(MAIN_FILES
  src/main.cpp
  src/manager.cpp
  src/router.cpp
)

add_executable(main ${MAIN_FILES})
target_include_directories(main PRIVATE include)
