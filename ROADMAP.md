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

Current verification baseline:

- `colcon build --symlink-install`: all five packages build successfully;
- `colcon test`: 53 tests, 0 errors, 0 failures and 3 skipped copyright checks;
- `cargo_bot_world`: `ament_flake8` and `ament_pep257` now pass;
- `learning`: `ament_flake8` now passes;
- 42 deterministic unit tests now cover geometry, kinematics and manipulator command logic.

#### Working rule

Only one stabilization step is implemented at a time. Before each step:

1. agree on its scope and expected result;
2. change only files required by that step;
3. run the checks defined for that step;
4. review the diff and test results;
5. mark the step complete only after confirmation, then discuss the next one.

#### 8.1 Clean up duplicate world-builder definitions — first

Goal: remove accidental duplicate constants and function definitions without changing the
generated indoor world.

Implementation plan:

1. Inspect `scripts/world_builder/furniture.py` and identify which duplicated definitions are
   actually active at runtime.
2. Keep one canonical implementation of each constant and factory function.
3. Preserve the dimensions and generated SDF behaviour currently used by the room definitions.
4. Generate all room models before and after the cleanup and compare their resulting SDF files.
5. Run the `cargo_bot_world` style tests and record the remaining failures for step 8.2.

Acceptance criteria:

- [x] No duplicate definitions remain in `furniture.py`
- [x] World generation completes without errors
- [x] Generated room SDF files are unchanged, except for intentionally reviewed formatting
- [x] No room, furniture or collision geometry is removed
- [x] The diff contains only world-builder cleanup required by this step

#### 8.2 Fix `cargo_bot_world` style checks

Goal: make `ament_flake8` and `ament_pep257` pass for the world package without changing its
behaviour.

Implementation plan:

1. Fix import grouping/order and unused imports.
2. Normalize whitespace, line length and quoting.
3. Correct docstrings required by `pep257`.
4. Format launch files and world-builder modules consistently.
5. Re-run only the `cargo_bot_world` tests, then run world generation once more.

Acceptance criteria:

- [x] `cargo_bot_world` flake8 test passes
- [x] `cargo_bot_world` pep257 test passes
- [x] World generation still succeeds
- [x] Generated geometry is unchanged

Completed in four reviewed substeps: furniture cleanup, core world-builder modules, room
definitions, and launch/generator/setup files. Final result: 3 tests, 0 failures, 1 skipped
copyright test pending the license decision in step 8.4.

#### 8.3 Fix `learning` style checks

Goal: make the educational package pass its existing lint suite without altering the examples.

Implementation plan:

1. Fix import grouping/order and long lines.
2. Preserve topic, service, action and parameter names.
3. Run the `learning` package tests.

Acceptance criteria:

- [x] `learning` flake8 test passes
- [x] Existing example entry points remain unchanged
- [x] No example behaviour is intentionally modified

Completed by reordering imports and wrapping one long service-construction line. Final result:
3 tests, 0 failures, 1 skipped copyright test pending the license decision in step 8.4.

#### 8.4 Complete package metadata and dependencies

Goal: make package manifests describe what the packages actually require at runtime.

Implementation plan:

1. Choose and document the repository/package license before replacing license placeholders.
2. Replace `TODO` descriptions in `package.xml` and Python `setup.py` files.
3. Add missing runtime dependencies, especially for `cargo_bot_world` launch files.
4. Check manifests with the available ROS package/lint tooling.
5. Build the workspace from the declared package graph.

Dependencies to verify include `launch`, `launch_ros`, `ament_index_python`, `xacro`,
`robot_state_publisher`, `ros_gz_sim`, `ros_gz_bridge`, `cargo_bot` and
`cargo_bot_interfaces`.

Acceptance criteria:

- [x] No project-owned package metadata contains `TODO`
- [x] Runtime dependencies used by launch files are declared
- [x] The selected license is applied consistently
- [x] A clean workspace build succeeds

Completed with Apache-2.0 for project-owned files and a separate third-party notice for the AWS
RoboMaker warehouse assets. Package descriptions and direct runtime dependencies now match the
implementation; both interface packages export `rosidl_default_runtime`. All five package
manifests pass XML validation, the workspace builds successfully, and the complete test result is
9 tests, 0 failures, 3 skipped copyright checks.

#### 8.5 Add unit tests for core logic

Goal: cover deterministic logic without starting RViz or Gazebo.

Initial test targets:

- geometry YAML loading and manipulator limit extraction;
- yaw-to-quaternion and differential-drive calculations;
- manipulator state transitions: start, finish, cancel and busy state;
- interpolation boundaries and invalid command validation where practical.

Implementation approach:

1. Extract small pure helpers only when needed to make behaviour testable.
2. Add focused tests with explicit inputs and expected outputs.
3. Avoid ROS graph and timing dependencies in unit tests.
4. Run package tests after every small test group.

Acceptance criteria:

- [x] Core kinematic math has deterministic tests
- [x] Manipulator state transitions have deterministic tests
- [x] Tests cover normal input and important boundary/error cases
- [x] All unit and existing style tests pass

First test group completed: the yaw/quaternion conversion, angle normalization, Euler pose update
and body-to-wheel velocity conversion are isolated as pure helpers and covered by 8 deterministic
tests.

Second test group completed: the project geometry YAML now has tests for manipulator limits, joint
names, passive wheel defaults, numeric conversion and incomplete input. The complete workspace
result after this group was 22 tests, 0 failures, 3 skipped copyright checks.

Third test group completed: the manipulator state store now has deterministic coverage for initial
state, copied snapshots, start, position update, finish, cancellation, busy state and stale
operation protection.

Fourth test group completed: position interpolation and command validation are covered at valid
boundaries and for unknown elements, missing limits, busy elements, out-of-range positions,
negative durations, `NaN` and infinity. Step 8.5 is complete with 42 deterministic unit tests; the
complete workspace result is 51 tests, 0 failures, 3 skipped copyright checks.

#### 8.6 Add launch smoke tests

Goal: catch missing executables, dependencies, parameters and topic wiring.

Candidate smoke tests:

- start the RViz drive stack without opening the RViz GUI;
- verify expected nodes and `/cmd_vel`, `/odom`, `/joint_states` topics;
- start a headless Gazebo world when practical;
- verify that the robot description parses and the spawn/bridge configuration is valid.

Acceptance criteria:

- [x] Main non-GUI RViz nodes start and stop cleanly
- [x] Expected core topics appear
- [x] URDF/Xacro parsing is covered
- [x] At least one Gazebo launch path has an automated or documented repeatable smoke check

First launch-test group completed: `drive_in_rviz.launch.py` keeps RViz enabled by default and now
supports `use_rviz:=false` for headless checks. The smoke test verifies clean startup and shutdown
of `robot_state_publisher`, `simple_diff_drive_sim` and `manipulator_control_node`, successful Xacro
evaluation, absence of the RViz process, the expected topic types, and a complete manipulator joint
state. This coverage was strengthened after the final visual check exposed a disconnected white
manipulator in the drive launch. The complete workspace result after this group was 52 tests, 0
failures, 3 skipped copyright checks.

Second launch-test group completed: `gazebo_warehouse.launch.py` keeps its GUI behaviour by default
and supports `headless:=true` for a server-only simulation that starts immediately. The automated
smoke test verifies that Gazebo loads the world, accepts the `cargo_bot` entity, creates the
`/clock` and `/odom` bridges, and starts the manipulator node. Exit codes from the external Gazebo
and bridge processes are not asserted because the Jazzy processes can terminate by signal during
the simultaneous `launch_testing` shutdown. Step 8.6 is complete; the full workspace result is
53 tests, 0 failures, 3 skipped copyright checks.

#### 8.7 Final stabilization verification

Goal: establish the clean baseline used by all later milestones.

Implementation plan:

1. Run a full `colcon build --symlink-install`.
2. Run the complete `colcon test` suite and inspect `colcon test-result --verbose`.
3. Manually smoke-check the documented RViz and Gazebo launch commands if a GUI is available.
4. Update README and this roadmap with the final verified status.

Acceptance criteria:

- [x] All five packages build successfully
- [x] `colcon test` reports zero failures
- [x] Main documented launch commands are verified
- [x] README and ROADMAP match the final implementation

Automated verification completed: all five launch files expose their expected arguments, all five
packages build successfully, and the complete test suite reports 53 tests, 0 failures and 3
skipped copyright checks.

Manual verification completed: the corrected `drive_in_rviz.launch.py` has been confirmed to
show the complete robot with the manipulator attached and correctly coloured. A lingering Gazebo
warehouse server was also found to capture the subsequent indoor launch; the two world launch
files now use separate Gazebo Transport partitions. During the indoor drive check, the
bidirectional `/joint_states` bridge caused `parameter_bridge` to exit after receiving
`/cmd_vel`; both Gazebo launches now bridge joint states only from Gazebo to ROS 2. The updated
package passes all 53 tests, and manual driving through `/cmd_vel` was verified in the indoor
world. Physical manipulator control in Gazebo remains outside stabilization and is tracked in
milestone 12. The README now contains a single testing and verification section covering the full
baseline, package and focused test runs, deterministic world generation, and manual smoke checks.

Expected stabilization result: the existing project has a reproducible green baseline before new
robot capabilities are introduced.

### 9. Lidar simulation

Add the first real simulated sensor because it directly unlocks mapping and navigation.

- [ ] Add a separate `cargo_bot_sensors.xacro` module
- [ ] Add a lidar link and Gazebo ray/GPU-lidar sensor
- [ ] Bridge `sensor_msgs/LaserScan` on `/scan`
- [ ] Document the sensor frame, update rate, range and topic
- [ ] Visualize scans in RViz

Expected result: `/scan` contains valid obstacle ranges and can be inspected in RViz while the
robot moves through the indoor world.

### 10. SLAM and map creation

- [ ] Add SLAM Toolbox runtime configuration
- [ ] Run SLAM Toolbox in the indoor world
- [ ] Verify the `map -> odom -> base_footprint` TF chain
- [ ] Drive the complete circular route and inspect loop closure
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

### 12. Physical Gazebo manipulator control

Connect the existing manipulator action API to simulated joint actuators after the mobile robot
navigation path is working.

- [ ] Choose `gz_ros2_control`/`ros2_control` or Gazebo joint controller systems
- [ ] Add controller configuration for rotation, lift, arm and gripper joints
- [ ] Use simulated joint states as feedback instead of treating commands as state
- [ ] Reduce the temporary high joint damping after controllers are active
- [ ] Preserve action cancellation, limits and concurrent independent movement
- [ ] Add a Gazebo manipulation launch/test scenario

Expected result: manipulator commands move the physical Gazebo links and report measured state.

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
