cmake_minimum_required(VERSION 3.20)
project(ASC_ode)

set (CMAKE_CXX_STANDARD 20)


include_directories(src nanoblas/src)

add_subdirectory (nanoblas)


add_executable (test_ode demos/test_ode.cpp)
target_link_libraries (test_ode PUBLIC nanoblas)

add_executable (demo_autodiff demos/demo_autodiff.cpp)
target_link_libraries (demo_autodiff PUBLIC nanoblas)


add_executable(convergence demos/convergence.cpp)
target_link_libraries(convergence PRIVATE nanoblas)
add_executable(test_rc demos/test_rc.cpp)
target_link_libraries(test_rc PRIVATE nanoblas)

include(CTest)
if(BUILD_TESTING)
  find_package(Catch2 3 QUIET)
  if(NOT Catch2_FOUND)
    include(FetchContent)
    FetchContent_Declare(Catch2
      GIT_REPOSITORY https://github.com/catchorg/Catch2.git
      GIT_TAG 56809e5282f104c5c8b570e7c2996cdc352d94f1 # v3.8.1
      GIT_SHALLOW FALSE)
    FetchContent_MakeAvailable(Catch2)
    list(APPEND CMAKE_MODULE_PATH "${catch2_SOURCE_DIR}/extras")
  endif()
  add_executable(ode_tests tests/test_timestepper.cpp)
  target_link_libraries(ode_tests PRIVATE nanoblas Catch2::Catch2WithMain)
  include(Catch)
  catch_discover_tests(ode_tests)
endif()
