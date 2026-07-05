cmake_minimum_required(VERSION 3.8)
project(cargo_bot_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ManipulatorElementState.msg"
  "action/MoveManipulatorElement.action"
  "srv/CancelManipulatorOperation.srv"
  "srv/GetManipulatorState.srv"
)

ament_package()
