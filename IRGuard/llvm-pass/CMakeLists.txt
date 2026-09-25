cmake_minimum_required(VERSION 3.20)

project(IRGuardMathPass LANGUAGES C CXX)

find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "LLVM_DIR = ${LLVM_DIR}")

list(APPEND CMAKE_MODULE_PATH "${LLVM_CMAKE_DIR}")

include(AddLLVM)

include_directories(SYSTEM ${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})

add_llvm_pass_plugin(
    IRGuardMathPass
    IRGuardMathPass.cpp
)

set_target_properties(
    IRGuardMathPass
    PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED YES
)
