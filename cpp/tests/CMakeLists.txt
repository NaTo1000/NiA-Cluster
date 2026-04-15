cmake_minimum_required(VERSION 3.20)

add_executable(nia-cluster-tests
    test_main.cpp
    test_message_types.cpp
    test_cluster_relay.cpp
    test_cluster_node.cpp
    test_integration.cpp
)

target_link_libraries(nia-cluster-tests PRIVATE
    nia-cluster-lib
    GTest::gtest
    GTest::gtest_main
)

target_include_directories(nia-cluster-tests PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

include(GoogleTest)
gtest_discover_tests(nia-cluster-tests)
