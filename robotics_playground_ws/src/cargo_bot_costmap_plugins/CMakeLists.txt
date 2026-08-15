cmake_minimum_required(VERSION 3.8)
project(cargo_bot_costmap_plugins)

find_package(ament_cmake REQUIRED)
find_package(nav2_costmap_2d REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)

add_library(persistent_obstacle_layer SHARED
  src/persistent_obstacle_layer.cpp
)
target_include_directories(persistent_obstacle_layer PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(persistent_obstacle_layer
  nav2_costmap_2d
  nav_msgs
  pluginlib
  rclcpp
)

pluginlib_export_plugin_description_file(
  nav2_costmap_2d persistent_obstacle_plugins.xml
)

install(TARGETS persistent_obstacle_layer
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
install(DIRECTORY include/ DESTINATION include)

ament_export_include_directories(include)
ament_export_libraries(persistent_obstacle_layer)
ament_export_dependencies(nav2_costmap_2d nav_msgs pluginlib rclcpp)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_persistent_obstacle_layer
    test/test_persistent_obstacle_layer.cpp
  )
  target_link_libraries(test_persistent_obstacle_layer
    persistent_obstacle_layer
  )
  ament_target_dependencies(test_persistent_obstacle_layer
    nav2_costmap_2d
    nav_msgs
    rclcpp
  )
endif()

ament_package()
