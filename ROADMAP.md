# ROS 2 Robotics Playground Roadmap

## Project overview

Self-contained ROS 2 learning and simulation project for Ubuntu 24.04 without physical hardware.
The workspace is located at `robotics_playground_ws/` and is built with `colcon`.

- **ROS 2:** Jazzy
- **Gazebo:** Harmonic through `ros_gz`
- **Language:** Python; URDF/Xacro and SDF for robot and world descriptions
- **Documentation:** [README.md](README.md)

Current packages:

| Package | Purpose |
|---|---|
| `learning` | Small ROS 2 examples for core concepts |
| `learning_interfaces` | Custom interfaces used by `learning` |
| `cargo_bot` | Robot model, RViz scenes, kinematic drive and manipulator control |
| `cargo_bot_interfaces` | Manipulator action, services and state message |
| `cargo_bot_world` | Gazebo warehouse and multi-room environments |

## Current status

The project currently supports three levels of simulation:

1. RViz model inspection with manual joint sliders.
2. RViz-only kinematic driving and manipulator visualization.
3. Gazebo driving with differential-drive physics and collision-enabled environments.

The robot can be driven manually through `/cmd_vel` in RViz and Gazebo. The manipulator action
API controls joint-state visualization in RViz. A physical Gazebo controller for the manipulator,
sensors, SLAM and autonomous navigation are not implemented yet.

## Completed

### 1. Core ROS 2 concepts

The `learning` and `learning_interfaces` packages contain working examples of:

- [x] Topics and publisher/subscriber nodes
- [x] Services and clients
- [x] Actions with feedback and cancellation
- [x] Runtime parameters and a parameter client
- [x] Launch files with arguments and includes
- [x] Lifecycle nodes
- [x] QoS compatibility and queue-depth experiments
- [x] Rosbag recording, inspection and playback documentation
- [x] Single- and multi-threaded executor examples
- [x] Diagnostics through `/diagnostics`
- [x] Custom message, service and action interfaces

### 2. Cargo Bot visual model

- [x] Create the `cargo_bot` package
- [x] Split the URDF/Xacro model into base, wheels, manipulator, materials and inertia modules
- [x] Add `base_footprint`, `base_link`, chassis and cargo deck
- [x] Add two drive wheels and a fixed rear support sphere
- [x] Add development and production visual modes
- [x] Add collision geometry and approximate inertial properties
- [x] Add RViz launch and configuration files

Current robot layout:

- heavy low warehouse chassis;
- two front differential-drive wheels;
- fixed spherical rear support;
- rear cargo deck;
- front lift/rotate/telescope/gripper manipulator;
- fixed camera-shaped link near the gripper, without a sensor plugin.

### 3. TF and kinematic movement in RViz

- [x] Store shared geometry in `config/cargo_bot_geometry.yaml`
- [x] Subscribe to `/cmd_vel`
- [x] Integrate differential-drive motion in `simple_diff_drive_sim`
- [x] Publish `odom -> base_footprint`
- [x] Publish `nav_msgs/Odometry` on `/odom`
- [x] Publish wheel positions on `/joint_states`
- [x] Add `drive_in_rviz.launch.py`
- [x] Document teleoperation and TF inspection

### 4. Manipulator model and RViz control

- [x] Add rotation, lift, telescoping arm and gripper joints
- [x] Add `MoveManipulatorElement.action`
- [x] Add `CancelManipulatorOperation.srv`
- [x] Add `GetManipulatorState.srv`
- [x] Validate element names, finite values and joint limits
- [x] Generate operation IDs and track per-element state
- [x] Allow different elements to move concurrently
- [x] Reject a second operation for an already-moving element
- [x] Support cancellation by operation ID
- [x] Interpolate positions linearly over the requested duration
- [x] Publish manipulator joint states for RViz
- [x] Publish passive wheel states separately
- [x] Add `manipulator_in_rviz.launch.py`

Current limitation: this controller publishes desired joint states for visualization. It is not a
Gazebo effort/velocity/position controller and does not provide physical manipulation.

### 5. RViz warehouse scene

- [x] Publish a warehouse floor, walls, shelves, boxes and loading zone as `MarkerArray`
- [x] Split marker factories by object type
- [x] Add `warehouse_in_rviz.launch.py`
- [x] Run the drive and manipulator nodes together with the scene

This environment is visual only. RViz markers do not participate in collision detection.

### 6. Gazebo robot simulation

- [x] Add collision and inertia to the robot model
- [x] Add the Gazebo differential-drive system plugin
- [x] Bridge `/cmd_vel`, `/odom`, `/tf`, `/joint_states` and `/clock`
- [x] Spawn the robot through `ros_gz_sim`
- [x] Drive using the same `/cmd_vel` interface as the RViz simulation
- [x] Verify collisions with floors, walls and shelves

The drive base uses Gazebo physics. Manipulator joints currently rely on high damping and do not
have a physical controller.

### 7. Gazebo environments

#### AWS warehouse

- [x] Create the `cargo_bot_world` package
- [x] Adapt the AWS RoboMaker warehouse assets for Gazebo Harmonic
- [x] Add `small_warehouse.sdf`
- [x] Add collision-enabled static walls, shelves and ground
- [x] Add `gazebo_warehouse.launch.py`

#### Multi-room indoor world

- [x] Create seven rooms, a corridor and an outdoor ground model
- [x] Provide a circular A → B → D → corridor → E → C → A route
- [x] Add dead-end rooms F and G
- [x] Split the building into independently generated models
- [x] Add shelves, boxes, desks, chairs and plants
- [x] Scale the layout for a roughly 1 m wide robot
- [x] Add the Python parametric world builder
- [x] Add `indoor_rooms.launch.py`

Current generated dimensions:

- Room A: 12 × 12 m
- Rooms B–G: 7.5 × 7.5 m
- Corridor: approximately 12 × 3 m
- Door openings: 2.7 m wide

## Next milestones

### 8. Project stabilization — next

Bring the existing implementation to a clean, reproducible baseline before adding navigation.

- [ ] Fix current `ament_flake8` and `ament_pep257` failures
- [ ] Remove duplicate definitions from the world-builder modules
- [ ] Add complete runtime dependencies to package manifests
- [ ] Replace placeholder package descriptions and licenses
- [ ] Add unit tests for geometry loading, differential-drive math and manipulator state handling
- [ ] Add launch/integration smoke tests for the main RViz and Gazebo configurations
- [ ] Keep README and ROADMAP status sections synchronized

Expected result: `colcon build` and `colcon test` finish successfully with no failed tests.

### 9. Physical Gazebo manipulator control

Connect the existing manipulator action API to simulated joint actuators.

- [ ] Choose `gz_ros2_control`/`ros2_control` or Gazebo joint controller systems
- [ ] Add controller configuration for rotation, lift, arm and gripper joints
- [ ] Use simulated joint states as feedback instead of treating commands as state
- [ ] Reduce the temporary high joint damping after controllers are active
- [ ] Preserve action cancellation, limits and concurrent independent movement
- [ ] Add a Gazebo manipulation launch/test scenario

Expected result: manipulator commands move the physical Gazebo links and report measured state.

### 10. Lidar and mapping

Add the first real simulated sensor because it directly unlocks mapping and navigation.

- [ ] Add a separate `cargo_bot_sensors.xacro` module
- [ ] Add a lidar link and Gazebo ray/GPU-lidar sensor
- [ ] Bridge `sensor_msgs/LaserScan` on `/scan`
- [ ] Document the sensor frame, update rate, range and topic
- [ ] Visualize scans in RViz
- [ ] Run SLAM Toolbox in the indoor world
- [ ] Save and version the generated map

Expected result: the robot can build a consistent map while being driven manually.

### 11. Nav2 autonomous navigation

- [ ] Add Nav2 and SLAM Toolbox runtime dependencies
- [ ] Configure robot footprint, velocity limits and costmaps
- [ ] Configure localization against the saved map
- [ ] Add a Nav2 bringup launch file for `indoor_rooms.sdf`
- [ ] Send `NavigateToPose` goals from RViz
- [ ] Verify navigation through doors and around furniture
- [ ] Document startup and troubleshooting

Expected result: the robot autonomously reaches goals in the multi-room environment.

## Later improvements

These items should follow a concrete navigation or manipulation use case:

- [ ] Named manipulator poses such as `stowed`, `pickup` and `cargo_place`
- [ ] Coordinated multi-joint commands and smoother motion profiles
- [ ] Rear cargo bin/tray design
- [ ] Dynamic boxes or pallets that can be pushed
- [ ] Gripper/object interaction and attachment logic
- [ ] Camera or depth camera near the gripper
- [ ] IMU and contact/bumper sensors
- [ ] Additional apartment-like environment if needed

## Current package structure

```text
robotics_playground_ws/src/
├── learning/                  # ROS 2 concept examples
├── learning_interfaces/       # learning custom interfaces
├── cargo_bot/                 # robot, RViz and control nodes
├── cargo_bot_interfaces/      # manipulator custom interfaces
└── cargo_bot_world/           # Gazebo worlds, models and world builder
```

The RViz-only and Gazebo drive modes intentionally share the `/cmd_vel` interface:

- `cargo_bot/warehouse_in_rviz.launch.py` — visual environment and kinematic movement;
- `cargo_bot_world/gazebo_warehouse.launch.py` — warehouse physics;
- `cargo_bot_world/indoor_rooms.launch.py` — multi-room physics environment.
