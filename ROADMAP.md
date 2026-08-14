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
| `cargo_bot_navigation` | SLAM mapping and future Nav2 configuration |

## Current status

The project currently supports three levels of simulation:

1. RViz model inspection with manual joint sliders.
2. RViz-only kinematic driving and manipulator visualization.
3. Gazebo driving with differential-drive physics and collision-enabled environments.

The robot can be driven manually through `/cmd_vel` in RViz and Gazebo. The manipulator action
API controls joint-state visualization in RViz. A physical Gazebo controller for the manipulator,
global map localization and autonomous navigation are not implemented yet. Live SLAM mapping is
implemented, but the complete route and canonical indoor map still require manual review. Lidar,
IMU, encoder odometry, deterministic noise/source substitution and EKF local odometry are
implemented and form the verified navigation-sensor baseline.

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

### 8. Project stabilization — complete

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

### 9. Navigation sensor foundation — complete

Add the three sensor sources needed by the mobile navigation path: a 2D lidar, an IMU containing
accelerometer and gyroscope measurements, and wheel encoders derived from simulated wheel joint
positions. Keep sensor sources, optional noise processing and navigation-facing topics separate so
that Gazebo, deterministic test publishers, rosbag playback and future hardware drivers can be
substituted without changing SLAM or Nav2 configuration.

#### Working rule

Only one sensor step is implemented at a time. Before each step:

1. agree on its exact scope and expected topic/frame contract;
2. change only the files required by that step;
3. implement the deterministic ideal path before adding noise or faults;
4. run the unit, launch and manual checks defined for that step;
5. review the diff and results;
6. mark the step complete only after confirmation, then select the next step.

#### Target interfaces

| Data | Source-side topic | Stable navigation-facing topic | ROS message |
|---|---|---|---|
| 2D lidar | `/sim/scan` | `/scan` | `sensor_msgs/msg/LaserScan` |
| IMU | `/sim/imu` | `/imu/data_raw` | `sensor_msgs/msg/Imu` |
| Wheel joint state | `/sim/joint_states` | internal input | `sensor_msgs/msg/JointState` |
| Encoder odometry | derived from wheel joints | `/wheel/odometry` | `nav_msgs/msg/Odometry` |
| Fused local odometry | wheel odometry + IMU | `/odometry/filtered` | `nav_msgs/msg/Odometry` |
| Simulator truth | Gazebo pose/odometry | `/ground_truth/odometry` | `nav_msgs/msg/Odometry` |

The source-side names are private simulation inputs. The navigation-facing names are the stable
contract used by later SLAM and Nav2 launches. Source selection and remapping must not require
changes to consumers.

#### Sensor profiles

The completed sensor stack will expose named profiles:

- `ideal` — deterministic measurements without injected noise or faults;
- `realistic` — moderate configurable bias, noise and quantization;
- `harsh` — stronger errors and optional dropouts for robustness experiments.

All stochastic processing must accept an explicit random seed. Gazebo-native noise and ROS-side
noise processing must not be enabled simultaneously for the same measurement.

#### 9.1 Define sensor structure and contracts

Goal: introduce the shared sensor description and configuration structure without publishing new
sensor data yet.

Implementation plan:

1. Add `urdf/cargo_bot_sensors.xacro` and include it from the main robot Xacro.
2. Add fixed `lidar_link` and `imu_link` frames with placement stored in shared geometry/config.
3. Add sensor measurement configuration for frame names, topics, update rates and ranges.
4. Reserve sensor profile and random-seed configuration keys without activating noise yet.
5. Document ownership of every source and public topic to avoid duplicate publishers.

Acceptance criteria:

- [x] The robot description contains `lidar_link` and `imu_link`
- [x] Sensor placement and measurement parameters are not duplicated across files
- [x] Xacro evaluation and the existing launch smoke tests still pass
- [x] TF connects both sensor frames to `base_link`
- [x] No new sensor topic is claimed to work before its implementation step

Completed with a separate sensor-frame Xacro module, physical placement in the shared geometry
file and measurement/interface contracts in `config/sensors.yaml`. The compact front-centre lidar
sits directly on the fixed chassis with its scan plane 0.3875 m above the ground; the IMU frame is
inside the chassis near its centre. No Gazebo sensor plugin or new topic publisher is enabled yet.
Five deterministic tests cover the links,
fixed joints, origins, placement, topic contract and absence of premature sensor elements. The
package builds successfully, `check_urdf` confirms the complete TF tree, and the accumulated test
result is 58 tests, 0 failures and 3 skipped copyright checks.

#### 9.2 Add ideal 2D lidar

Goal: publish deterministic planar obstacle ranges from Gazebo and visualize them in RViz.

Implementation plan:

1. Add a Gazebo GPU lidar sensor to `lidar_link`.
2. Bridge Gazebo data one way into the source-side scan topic.
3. Expose the stable `/scan` interface through the sensor launch layer.
4. Add an RViz LaserScan display.
5. Verify that the robot body and manipulator do not unintentionally block the required field of
   view; preserve intentional occlusion if selected during placement review.

Acceptance criteria:

- [x] `/scan` publishes `sensor_msgs/msg/LaserScan`
- [x] Scan frame, angular limits, range limits, sample count and update rate match configuration
- [x] Finite ranges respond to known collision geometry in a Gazebo world
- [x] `NaN`, infinity and out-of-range values follow the documented policy
- [x] RViz displays scans in the correct position relative to the robot
- [x] Unit and headless Gazebo smoke tests cover the scan contract

Implementation and automated verification are complete. Both Gazebo worlds load the Ogre2 sensor
system; the robot publishes an ideal 15 Hz, 720-sample, 360-degree GPU lidar scan on `/sim/scan`.
A one-way bridge fixes the ROS frame to `lidar_link`, and `lidar_relay` forwards measurements
unchanged to `/scan`. The headless warehouse test receives a real scan, verifies its frame, shape,
0.15–20 m limits and finite obstacle ranges. Saved RViz drive and warehouse scenes contain a
reliable LaserScan display. Manual verification confirmed the coloured robot model, complete wheel
transforms and red scan points in the correct RViz scene. The saved RViz QoS contract is covered by
two additional tests. The accumulated result is 66 tests, 0 failures and 3 skipped copyright
checks. Gazebo now also publishes both drive-wheel joint states, which keeps their RViz transforms
complete and provides the future encoder input. Step 9.2 is complete.

#### 9.3 Add ideal IMU

Goal: publish deterministic accelerometer, gyroscope and orientation data through the standard ROS
IMU message.

Implementation plan:

1. Add a Gazebo IMU sensor to `imu_link`.
2. Bridge Gazebo data one way into the source-side IMU topic.
3. Expose `/imu/data_raw` with a documented frame, update rate and covariance policy.
4. Verify axis signs and units at rest, during straight motion and during rotation.
5. Initially keep acceleration out of the odometry filter until its gravity and covariance
   handling are explicitly configured and tested.

Acceptance criteria:

- [x] `/imu/data_raw` publishes `sensor_msgs/msg/Imu`
- [x] Frame, update rate, units and covariance policy are documented and tested
- [x] Stationary, accelerating and rotating behaviour matches the documented axis conventions
- [x] Quaternion data is valid whenever orientation is reported
- [x] Unit and launch tests cover the IMU contract

Completed with a Gazebo IMU system in both worlds, an IMU sensor on `imu_link`, a one-way bridge
to `/sim/imu` and an ideal relay publishing reliable `/imu/data_raw`. The relay preserves all
measurements and applies explicit positive covariance diagonals from `config/sensors.yaml`.
Deterministic unit tests cover configuration validation and covariance expansion. The headless
Gazebo test verifies the frame, normalized quaternion, covariance, near-zero stationary linear
acceleration, non-zero forward acceleration response and positive `angular_velocity.z` during a
left turn. Step 9.3 is complete with 72 tests, 0 failures and 3 skipped copyright checks.

#### 9.4 Derive odometry from wheel encoders

Goal: calculate local wheel odometry from left and right wheel joint positions instead of treating
the ready-made Gazebo pose estimate as encoder output.

Implementation plan:

1. Consume only the configured left and right wheel joints from the source joint-state topic.
2. Convert wheel angles to configurable integer encoder ticks.
3. Reuse the shared wheel radius and separation from robot geometry.
4. Integrate differential-drive motion and publish `/wheel/odometry`.
5. Preserve the ready-made Gazebo odometry separately as ground truth for comparisons.

Acceptance criteria:

- [x] Straight, arc and in-place rotation calculations have deterministic unit tests
- [x] Encoder resolution is configurable and quantization is tested
- [x] Missing joints, first sample and invalid/non-monotonic timestamps are handled safely
- [x] `/wheel/odometry` is derived from wheel measurements, not copied from Gazebo odometry
- [x] Ground-truth and encoder-derived odometry have separate topics and documented semantics

Status: complete. Gazebo publishes only the configured drive-wheel positions on
`/sim/joint_states`. The `wheel_odometry` node relays wheel measurements to the standard
`/joint_states` TF input alongside the independently published manipulator states, and quantizes
continuous angles at the configured 2048
ticks per revolution, integrates exact differential-drive increments using the shared `0.115 m`
wheel radius and `0.58 m` separation, and publishes `/wheel/odometry` without TF. The ready-made
Gazebo estimate is remapped to `/ground_truth/odometry`. Deterministic tests cover straight, arc and
in-place motion, configurable symmetric quantization, incomplete samples and invalid timestamps;
the headless Gazebo test confirms both independent odometry publishers. Step 9.4 is complete.
The accumulated regression result is 87 tests, 0 failures and 3 skipped copyright checks.

#### 9.5 Add deterministic noise profiles

Goal: inject configurable measurement imperfections without modifying sensor consumers.

Initial models:

- lidar: range Gaussian noise, constant bias and optional invalid/dropout samples;
- IMU: angular-velocity and acceleration noise, constant bias and optional slow bias drift;
- encoders: tick quantization, missed ticks and independent left/right scale error.

Implementation plan:

1. Implement noise math as pure functions independent of ROS nodes.
2. Add pass-through, `realistic` and `harsh` configuration profiles.
3. Preserve timestamps, frame IDs and message dimensions through processing.
4. Require a configurable seed for stochastic processing.
5. Reject configurations that enable both Gazebo-native and ROS-side noise for one measurement.

Acceptance criteria:

- [x] The `ideal` profile is an exact pass-through where applicable
- [x] Equal input, configuration and seed produce equal output
- [x] Noise statistics and boundary handling have deterministic tests
- [x] Invalid ranges and covariance remain standards-compliant
- [x] Switching profile does not change public topic names

Status: complete. Pure ROS-independent models now cover lidar Gaussian noise, bias and `+inf`
dropout; IMU white noise, constant bias and seeded bias drift; and encoder scale error plus missed
integer ticks. The `ideal`, `realistic` and `harsh` profiles share a configurable base seed while
using independent deterministic streams per sensor. Both Gazebo launches accept
`sensor_profile:=...`; a verified `realistic` launch retained `/scan`, `/imu/data_raw` and
`/wheel/odometry`. IMU covariance is never lower than the configured white-noise variance, and
configuration validation rejects simultaneous Gazebo-native and ROS-side noise.
The accumulated regression result is 104 tests, 0 failures and 3 skipped copyright checks.

#### 9.5.1 Add sensor diagnostics and live comparison

Goal: make ideal/noisy sensor behaviour and later filter improvements observable in real time with
a visualization matched to each data type.

Acceptance criteria:

- [x] Raw and processed lidar scans are overlaid with distinct colours and compatible QoS
- [x] Raw and processed gyroscope and accelerometer axes can be plotted live
- [x] Both wheel angles can be plotted live
- [x] Encoder odometry and Gazebo ground truth are shown as distinct bounded paths
- [x] Diagnostics use only `/debug/...` outputs and do not change navigation interfaces

Status: complete. `sensor_diagnostics.launch.py` starts an RViz comparison dashboard, separate
`rqt_plot` windows for gyroscope, accelerometer and wheel positions, and a bounded path publisher.
RViz shows raw/processed lidar in blue/red and encoder/ground-truth paths in orange/green. Every
window can be disabled independently for headless or focused diagnostics.
The accumulated regression result is 108 tests, 0 failures and 3 skipped copyright checks.

#### 9.6 Make sensor sources replaceable

Goal: switch an individual sensor between Gazebo, mock/test, rosbag and external inputs through
launch configuration and remapping.

Implementation plan:

1. Add independent `lidar_source`, `imu_source` and `encoder_source` launch selections.
2. Keep processing and public output topics unchanged across source choices.
3. Add deterministic publishers or fixtures for automated tests.
4. Document rosbag and external-driver remapping examples.
5. Detect or document duplicate-publication conflicts.

Acceptance criteria:

- [x] Each sensor source can be replaced independently
- [x] SLAM/navigation-facing topics remain unchanged
- [x] Mock inputs support deterministic headless tests
- [x] Source switching does not require editing Xacro or consumer configuration

Status: complete. Both Gazebo world launches expose independent `lidar_source`, `imu_source` and
`encoder_source` choices for `gazebo`, `mock`, `rosbag` and `external`. Relay and odometry nodes
resolve private inputs from `sensors.yaml` while continuing to own the single public `/scan`,
`/imu/data_raw` and `/wheel/odometry` interfaces. Gazebo bridges are conditional per sensor, and a
deterministic mock publisher supplies standard 720-ray `LaserScan`, stationary `Imu` and increasing
wheel `JointState` fixtures. A mixed integration run verified mock lidar and encoders alongside a
Gazebo IMU with only the required IMU bridge active. Rosbag remapping, external-driver conventions
and duplicate-publication constraints are documented.
The accumulated regression result is 124 tests, 0 failures and 3 skipped copyright checks.

#### 9.7 Fuse wheel odometry and IMU

Goal: publish the single local odometry estimate later consumed by SLAM and Nav2.

Implementation plan:

1. Add `robot_localization` EKF configuration in planar `two_d_mode`.
2. Initially fuse wheel odometry with IMU yaw rate; add other IMU fields only after review.
3. Publish `/odometry/filtered` and exactly one `odom -> base_footprint` transform.
4. Prevent Gazebo DiffDrive and the EKF from publishing the same TF.
5. Compare ideal and noisy estimates against `/ground_truth/odometry`.

Acceptance criteria:

- [x] The EKF consumes `/wheel/odometry` and `/imu/data_raw`
- [x] Only one node owns `odom -> base_footprint`
- [x] Filtered odometry remains continuous during the documented sensor profile
- [x] Automated checks compare filtered and encoder estimates with simulator ground truth
- [x] Later SLAM and Nav2 launches can depend only on `/scan`, `/odometry/filtered` and TF

Status: complete. A 50 Hz `robot_localization` EKF in `two_d_mode` fuses wheel `x`, `y`, `yaw`,
forward velocity and yaw rate with IMU yaw rate for `realistic` and `harsh`. The later SLAM
stabilization work added a profile-selected exact publisher for `ideal`; exactly one of it or the
EKF publishes `/odometry/filtered` and `odom -> base_footprint`. Gazebo DiffDrive outputs moved to
private `/wheel_model/*` topics, while a separate physical-pose OdometryPublisher supplies
`/ground_truth/odometry` for ideal mapping and comparison. Wheel messages
now carry explicit positive pose/twist covariance. Automated isolated Gazebo routes cover both
ideal and seeded `realistic` profiles, verify finite continuous output, and bound wheel/filtered
position error against simulator truth to `0.5 m` on the short routes. Physical wheel slip is
expected and remains visible on the separate diagnostic encoder stream. The
diagnostic RViz dashboard overlays wheel, EKF and truth trajectories in orange, purple and green.
The accumulated regression result is 129 tests, 0 failures and 3 skipped copyright checks.

#### 9.8 Final sensor verification and documentation

Goal: establish a tested sensor baseline before starting SLAM.

Implementation plan:

1. Run the complete build and test suite.
2. Run deterministic ideal-profile tests in the indoor world.
3. Run a seeded realistic-profile route and record comparison metrics.
4. Manually inspect lidar, TF and odometry in RViz.
5. Update README and this roadmap with final commands, interfaces, profiles and limitations.

Acceptance criteria:

- [x] All packages build and the complete test suite passes
- [x] Ideal and seeded realistic runs are repeatable
- [x] Sensor topics, frames, rates, noise profiles and source selection are documented
- [x] Ground-truth comparison results are recorded
- [x] The stack is ready for SLAM Toolbox without sensor architecture changes

Expected result: the robot exposes a replaceable and testable navigation sensor stack consisting
of `/scan`, `/imu/data_raw`, `/wheel/odometry` and `/odometry/filtered`, with deterministic ideal
operation, seeded noise profiles and separate physical simulator ground truth.

Status: complete. Headless launch tests cover the warehouse in `ideal` and seeded `realistic`
modes and the indoor world in `ideal` mode. The comparison reference is now the physical Gazebo
model pose rather than DiffDrive's wheel-integrated estimate. Exact ideal local odometry matches
that pose; bounded differences on `/wheel/odometry` expose expected chassis slip. RViz verification confirms lidar
returns and the separate wheel, EKF and ground-truth paths. Public sensor interfaces remain stable,
so SLAM Toolbox can consume `/scan`, `/odometry/filtered` and the existing TF tree without changing
the sensor-source architecture.

### 10. SLAM and map creation — in progress

Build and validate the indoor map through manual driving before introducing any autonomous
planning or motion. SLAM Toolbox owns `map -> odom`. `ideal_odometry` owns
`odom -> base_footprint` in the canonical `ideal` run; the EKF owns it in `realistic` and `harsh`.

#### Agreed design decisions

- Navigation configuration belongs to a new `cargo_bot_navigation` package.
- The canonical map is built first with `sensor_profile:=ideal`.
- `sensor_profile` remains a launch argument so `realistic` and `harsh` can be selected without
  editing launch or configuration files.
- Interactive mapping uses SLAM Toolbox `online_async` mode.
- Both the occupancy map and the serialized SLAM Toolbox pose graph are retained.
- Startup and interface contracts are automated; the complete route and initial map-quality
  review remain manual.
- Robot spawn pose, map name and map location are launch arguments with documented defaults, not
  constants embedded in launch code.

#### Target package and file structure

```text
robotics_playground_ws/src/cargo_bot_navigation/
├── cargo_bot_navigation/
│   ├── __init__.py
│   ├── map_io.py
│   └── save_slam_map.py
├── config/
│   └── slam_mapping.yaml
├── launch/
│   └── slam_mapping.launch.py
├── maps/
│   └── .gitkeep
├── rviz/
│   └── slam_mapping.rviz
├── test/
│   ├── test_slam_config.py
│   ├── test_map_io.py
│   ├── test_save_slam_map.py
│   └── test_launch_slam_mapping.py
├── package.xml
├── resource/cargo_bot_navigation
├── setup.cfg
└── setup.py
```

The `maps/` directory remains empty until step 10.3 produces reviewed map artifacts. The
`save_slam_map` helper writes a standard occupancy map directly from `/map` and asks SLAM Toolbox
to serialize the matching pose graph under the same safe base name.

#### Mapping launch contract

`slam_mapping.launch.py` will include the existing indoor-world launch instead of duplicating the
Gazebo, robot, bridge, sensor and EKF nodes. Its initial public arguments will be:

| Argument | Initial default | Purpose |
|---|---:|---|
| `spawn_x` | `0.0` | Robot start X position in the world |
| `spawn_y` | `0.0` | Robot start Y position in the world |
| `spawn_z` | `0.1` | Robot start height |
| `spawn_yaw` | `1.5708` | Robot start heading, facing north in room A |
| `sensor_profile` | `ideal` | Select `ideal`, `realistic` or `harsh` sensors |
| `headless` | `false` | Start Gazebo without its GUI when true |
| `use_rviz` | `true` | Start the mapping RViz view when true |
| `pose_graph` | empty | Pose-graph base path for continued mapping |
| `map_start_at_dock` | `false` | Match a loaded graph at its first node |

The four spawn arguments must also be added to `cargo_bot_world/indoor_rooms.launch.py` and passed
directly to `ros_gz_sim create`. Existing callers retain the current room-A pose through defaults.
Step 10.3 adds a separate save interface with `map_name:=indoor_rooms` and a configurable writable
`map_output_dir`; its default output is outside the installed package so experiments cannot
silently overwrite the canonical committed map. Map-loading arguments are deliberately deferred
to milestone 11 because milestone 10 builds a new map rather than localizing against an existing
one.

#### Required runtime graph

```text
/scan --------------------------> SLAM Toolbox ----------------> /map
                                      |
                                      └------------------------> map -> odom

Gazebo physical pose -------------> ideal_odometry (ideal) ----> /odometry/filtered
/wheel/odometry + /imu/data_raw --> EKF (realistic/harsh) -----> /odometry/filtered
                                      └------------------------> odom -> base_footprint

robot_state_publisher -----------------------------------------> base_footprint -> lidar_link
```

SLAM always consumes the stable `/odometry/filtered` and TF interfaces. In `ideal`, those are
derived from the true physical Gazebo model pose so wheel slip cannot rotate the scan; in
`realistic` and `harsh`, they come from the wheel/IMU EKF. Gazebo's private truth TF is never
bridged directly onto ROS `/tf`.

#### 10.1 Integrate SLAM Toolbox

- [x] Scaffold `cargo_bot_navigation` as an Apache-2.0 `ament_python` package
- [x] Declare direct runtime and test dependencies, including SLAM Toolbox
- [x] Parameterize the indoor-world spawn pose without changing its current defaults
- [x] Add and validate mapping configuration for `/scan`, `odom`, `base_footprint` and `map`
- [x] Include SLAM Toolbox in `online_async` mode with `use_sim_time:=true`
- [x] Add a mapping launch that includes the indoor world and forwards the agreed arguments
- [x] Add an RViz scene for the occupancy map, scan, robot model and TF
- [x] Verify `/map` and the complete `map -> odom -> base_footprint -> lidar_link` TF chain
- [x] Add a repeatable headless startup and interface check

Implementation order:

1. Create the package skeleton, installation rules and manifest.
2. Add spawn-pose arguments to the indoor launch and extend its existing tests to verify defaults
   and at least one override.
3. Add `slam_mapping.yaml` with only the parameters required for the existing lidar, odometry and
   frames; keep tuning values explicit and documented.
4. Add `slam_mapping.launch.py`, default it to `ideal`, and forward all world and sensor arguments
   instead of copying the indoor launch implementation.
5. Add the saved RViz mapping view while keeping `use_rviz:=false` suitable for automation.
6. Add configuration tests and one headless launch test.
7. Build all six packages, run the complete test suite, review the launch graph and document the
   exact command used to start manual mapping.

Automated checks for this step:

- mapping YAML contains the agreed topic and frame contract;
- invalid or incomplete project-owned configuration is rejected by focused tests;
- the indoor launch preserves its current default pose and accepts overridden pose values;
- the headless launch receives `/scan`, `/odometry/filtered` and a non-empty `/map`;
- TF lookup succeeds from `map` through `odom` and `base_footprint` to `lidar_link`;
- exactly one navigation-side component owns `map -> odom`, and exactly one profile-selected
  component owns `odom -> base_footprint`;
- all processes start and stop cleanly enough for the existing Jazzy launch-testing conventions.

Acceptance criteria:

- [x] All six packages build successfully
- [ ] The full regression suite reports zero errors and zero failures
- [x] `sensor_profile:=ideal` is the documented and tested default
- [x] `sensor_profile:=realistic` can be selected without editing any file
- [x] Spawn pose can be changed entirely through launch arguments
- [x] The headless SLAM graph publishes `/map` and the required TF chain
- [x] RViz is configured to display the live map and scan when enabled
- [x] No autonomous planner, controller or `NavigateToPose` component is introduced

Implementation status: the package, asynchronous mapping graph, parameterized spawn pose, saved
RViz scene and automated map/TF contract are complete. RViz fixes LaserScan rendering in `map`.
The ideal path now uses the Gazebo physical-pose OdometryPublisher rather than mislabeled DiffDrive
wheel odometry, and disables unnecessary scan-matcher corrections. The focused mapping launch test saves
a temporary occupancy map and pose graph and shuts down without leaving display processes. Latest
focused results are clean: `cargo_bot` 121 tests, `cargo_bot_world` 6 tests and
`cargo_bot_navigation` 32 tests, with zero errors and zero failures.

The exact implementation scope and acceptance thresholds for this step will be agreed before work
starts, following the same one-step-at-a-time rule used for stabilization and sensor development.

#### 10.2 Build the complete indoor map manually

- [ ] Start from a documented fixed pose in room A
- [ ] Drive the A → B → D → corridor → E → C → A loop manually
- [ ] Map the F and G dead ends and revisit shared areas from different directions
- [ ] Inspect loop closure, wall alignment, doors and navigable free space
- [ ] Record the sensor and TF inputs required for repeatable offline tuning

Implementation and review sequence:

1. Start with the default room-A pose and `sensor_profile:=ideal`.
2. Record `/scan`, `/tf`, `/tf_static`, `/odometry/filtered` and `/clock` while mapping.
3. Drive through the circular route, then cover F and G. The physical model is tuned for the
   documented 3.0 m/s linear and 1.0 rad/s angular commands; abrupt-stop pitch is limited by the
   robot's mass properties rather than hidden in the ideal sensor or TF pipeline.
4. Return to room A and inspect the loop closure before saving anything as canonical.
5. Tune one documented parameter group at a time and replay the recorded inputs where practical.
6. Repeat the accepted route with a fixed seeded `realistic` profile; this is a robustness check,
   not the source of the canonical map.

Map-quality review criteria:

- [ ] Major walls form single aligned boundaries after loop closure
- [ ] Door openings required by the route remain visibly open
- [ ] Rooms A–G and the corridor are represented without disconnected map islands
- [ ] The robot pose remains aligned with lidar returns in RViz
- [ ] The realistic-profile run remains usable without changing public topics or SLAM config files

#### 10.3 Save and validate the map

- [x] Save the occupancy map (`.yaml` and `.pgm` image) as a candidate artifact
- [x] Save the serialized SLAM Toolbox pose graph as a candidate artifact
- [ ] Reload both outputs in a fresh run
- [ ] Document the map resolution, origin, start pose and regeneration procedure
- [ ] Establish repeatable ideal and seeded realistic-profile mapping checks

Implementation order:

1. Save the reviewed occupancy map under the selected `map_name` and `map_output_dir`.
2. Serialize the corresponding SLAM Toolbox pose graph under the same base name.
3. Check that all referenced files are inside the package and install through `setup.py`.
4. Reload the occupancy map independently and verify its metadata and dimensions.
5. Reload the pose graph in SLAM Toolbox and verify that mapping can continue.
6. Add deterministic file-level checks for the map metadata and required artifacts.
7. Document creation, overwrite policy, reload and alternative output-directory commands.

Acceptance criteria:

- [x] Saving never silently overwrites the canonical committed map
- [ ] Occupancy-map YAML references a package-owned image with valid resolution and origin
- [ ] The pose graph reloads with the reviewed map geometry intact
- [x] `map_name` and `map_output_dir` work without editing launch or Python files
- [x] Generated maps outside the package can be used for experiments without affecting the
  canonical map

Implementation status: the parameterized `save_slam_map` command, safe overwrite policy,
portable PGM/YAML writer and pose-graph serialization are implemented and covered by unit and
headless integration tests. The candidate `saved_maps/indoor_map` set contains a 694 × 418 PGM at
0.05 m/cell plus matching YAML, posegraph and data files. `pose_graph` and `map_start_at_dock`
launch arguments support continued mapping. This step remains open until the candidate is copied
to the package as the reviewed canonical map and both occupancy-map loading and pose-graph
continuation are verified in a fresh manual run.

Expected result: the robot produces a consistent, reloadable indoor map through manual driving,
without autonomous planning or motion.

Physical mapping stability is shared by all sensor profiles. The tall manipulator mass was reduced
to about 77 kg, chassis centre of mass was lowered by 0.10 m, chassis roll/pitch inertia was raised
with a physically valid 2.0 multiplier, and the cargo deck mass was reduced to 80 kg. No extra
ground-contact support was retained because it impeded differential-drive rotation. The SLAM
integration test now includes 3.0 m/s forward motion, an abrupt stop and 1.0 rad/s rotation; it
requires both normal turning and less than 0.035 rad (about 2 degrees) of IMU pitch deviation.
The physical DiffDrive additionally limits forward acceleration to 2.0 m/s² and braking to
4.0 m/s² while preserving the 3.0 m/s top speed. In the measured `turn -> forward` transition this
reduced 0.5-second lateral drift from about 0.25 m to 0.01 m; rejected wheel-mass, passive-damping,
chassis-decay and extreme-friction variants were not retained because they performed worse.

For autonomous-navigation validation the physical model now uses a deliberately near-ideal
profile before the later 50% scale change: 120 kg chassis, 10 kg cargo deck, 8 kg drive wheels,
about 10.5 kg complete manipulator, low-friction rear ball support and the original forward
drive-axle position at `x=0.32 m`. Keeping the axle below the manipulator-side part of the chassis
and the ball at `x=-0.62 m` widens the
longitudinal support layout and reduces pitch rocking under acceleration and braking. The DiffDrive limits are
6.0 m/s² acceleration, 20.0 m/s² braking, 10.0 rad/s² angular acceleration and 15.0 rad/s² angular
braking. A flat-world regression passed: straight lateral and heading drift were zero, stop drift
was 0.189 m and a left/right figure eight closed within 0.244 m and 0.088 rad before the axle was
restored. With the forward axle, motion of `base_link` during an in-place turn is expected and must
not be classified as wheel skid. This profile is intentionally non-engineering and exists to
isolate Nav2 behavior from the earlier heavy-body dynamics.

The physical axle offset is represented explicitly by `base_axle`, currently fixed 0.16 m ahead of
`base_footprint`. Static localization, planning, control and costmaps use this axle control point;
SLAM and the world/model anchor remain unchanged. The same physical envelope is therefore
re-expressed for navigation as `x=-0.585..0.49 m`, `y=-0.33..0.33 m`.

The complete robot was subsequently scaled to 50% for indoor navigation. Link dimensions,
offsets, wheels, sensors, collision geometry, lidar self-filter masks and manipulator linear
travel all use scale 0.5. Masses use the constant-density scale 0.125 and generated inertias scale
approximately by 0.03125. The map and world are unchanged. At half scale `base_axle` is 0.16 m
ahead of `base_footprint`, and the same footprint becomes `x=-0.585..0.49 m`,
`y=-0.33..0.33 m`. Controller and inflation tuning were deliberately left unchanged for the next,
separately measured control-stability step.

Corridor tuning keeps the hard polygon footprint unchanged while reducing the local soft
inflation radius to 0.75 m and increasing local/global cost decay to 4.0. The required global
1.49 m radius is retained for the footprint-aware Smac heuristic. Global planning time is bounded
at 8.0 s after the former 2.0 s budget could not solve the far-left-room route. RPP collision
projection remains at 0.40 s to avoid premature stops on distant projected arcs.

Mapping scan density and robot self-filtering are also implemented. The lidar remains at 15 Hz and
720 horizontal samples, while SLAM accepts scans every 0.03 rad of rotation or 0.05 m of travel and
publishes the occupancy map every 0.25 s. `lidar_relay` preserves raw Gazebo data on `/sim/scan`
and removes `/scan` endpoints inside configurable chassis and wheel masks. The masks live in
`config/sensors.yaml`, so another robot geometry can supply its own exclusion boxes without code
changes. Unit tests cover mask loading and selective rejection; the Gazebo SLAM integration test
continues to verify mapping, motion, turning, TF alignment and bounded pitch.

### 11. Localization and path calculation without motion — implemented

Localize on the saved map and calculate collision-free global paths while keeping all autonomous
velocity output disabled. Static walls and furniture are handled here because path calculation
must already account for known obstacles.

#### 11.1 Localize on the saved map

- [x] Add the map server and an AMCL configuration for the differential-drive robot
- [x] Require a user map path and validate both its YAML and referenced image before startup
- [x] Apply one parameterized initial pose to Gazebo and AMCL
- [x] Set and reset the initial pose through RViz
- [ ] Verify that localization is stable in multiple rooms and along the circular route
- [ ] Compare the localized pose with `/ground_truth/odometry`
- [x] Ensure exactly one profile-appropriate source owns `map -> odom`

#### 11.2 Define footprint and global costmap

- [x] Define the Cargo Bot footprint from the robot geometry with a reviewed safety margin
- [x] Configure the static and inflation costmap layers
- [ ] Verify clearance through doors, the corridor and furnished rooms
- [x] Visualize the global costmap in RViz

#### 11.3 Calculate global paths

- [x] Start the Nav2 planner server without the controller or navigation command output
- [x] Convert every RViz `2D Goal Pose` click, including final yaw, into `ComputePathToPose`
- [x] Publish and visualize the newest successful result on `/planned_path`
- [ ] Verify paths do not cross inflated obstacles or leave known free space
- [x] Clear the previous path and reject goals outside the map or without a valid route
- [x] Add deterministic path-planning checks while the robot remains stationary
- [x] Verify that `/cmd_vel` has no publishers during the planning test

Implementation status: `path_planning.launch.py` requires a user-created map and starts the indoor
world, Map Server, AMCL, Planner Server with differential-drive Smac 2D, lifecycle manager and
`path_requester`. It does
not start Controller Server, BT Navigator, Behavior Server or Velocity Smoother. The same
`initial_pose_x/y/yaw` values configure the Gazebo spawn and AMCL, while RViz retains interactive
`2D Pose Estimate`. `2D Goal Pose` triggers an immediate calculation and displays the green path;
new or invalid goals clear the previous result. The headless integration test loads a test-only
map, verifies `map -> odom -> base_footprint`, creates a path with the requested final orientation,
checks invalid-goal clearing and asserts that `/cmd_vel` has no publishers.

For deterministic navigation, `ideal` uses a fixed identity `map -> odom` and disables AMCL's TF
broadcast, preventing particle-filter corrections from rotating or shifting a map built from exact
odometry. `realistic` and `harsh` retain AMCL as the transform owner. The rebuilt `indoor_map` was
checked directly after integration: `(0, 0)` is a valid spawn with about 3.14 m clearance to the
nearest non-free cell. Gazebo joint states are remapped into `robot_state_publisher`, so RViz
receives transforms for the wheels and articulated Cargo Bot links instead of reporting
missing-link TF errors.

Remaining manual acceptance checks:

- [ ] Verify localization stability in multiple rooms on the user's saved indoor map
- [ ] Compare AMCL with `/ground_truth/odometry` during a driven diagnostic run
- [ ] Review footprint clearance through every required doorway and corridor
- [ ] Calculate and visually review paths between representative real room pairs

Expected result: the robot is localized on the saved map and can calculate a valid global path to
a requested goal without moving.

### 12. Static-world trajectory execution — implemented

Follow validated paths in the unchanged indoor world before introducing unexpected or moving
obstacles.

#### 12.1 Configure path following

- [x] Add and tune the controller server for the differential-drive base
- [x] Apply conservative linear, angular and acceleration limits
- [x] Configure progress, goal and path-following tolerances
- [x] Complete goals by position within 0.30 m without circling for final yaw
- [x] Verify cancellation always stops the robot

#### 12.2 Validate representative trajectories

- [x] Test straight motion and cancellation with bounded velocity in an automated Gazebo launch
- [x] Test a corridor-exit turn and arrival in a neighbouring room in an automated Gazebo launch
- [x] Test a 180-degree axle turn with no more than 0.10 m axle displacement
- [ ] Test arcs and final orientation on representative user goals
- [x] Test a long automated route from the initial room into the furnished far-left room
- [ ] Test every remaining required door, corridor and furnished-room traversal
- [x] Measure straight-line path-tracking error and check for oscillation
- [x] Verify ground-truth arrival, clean goal/cancellation stops and motion-limit compliance
- [x] Check the complete rotated footprint against occupied map cells throughout the long route
- [x] Run every automated navigation scenario three times in isolated simulations
- [x] Clean up the exact Gazebo partition after successful, failed or interrupted launch tests

#### 12.3 Add complete `NavigateToPose` behaviour

- [x] Add the BT Navigator and a minimal reviewed recovery set
- [x] Send goals from RViz and the ROS action interface
- [ ] Navigate between every required room in the static world
- [x] Handle cancellation, invalid goals and unreachable goals explicitly
- [x] Document launch, operation and troubleshooting

Implementation status: `static_navigation.launch.py` reuses the validated map, AMCL and
differential-drive Smac 2D
stack and adds Regulated Pure Pursuit, a rolling static local costmap, Behavior Server, BT
Navigator and Velocity Smoother. Raw controller commands use `/cmd_vel_nav`; only bounded smoothed
commands reach `/cmd_vel`. `/cancel_navigation` cancels every active NavigateToPose goal, and the
launch test verifies physical displacement, configured speed bounds and a final zero Twist. The
manipulator home transform is rotated 180 degrees so the arm starts behind the mobile base.
The rebuilt indoor map uses its original mapping pose `(0.0, 0.0, 1.5708)` as the verified start.
PGM analysis measured about 3.14 m to the nearest non-free cell there; the former `(-2.0, -1.0)`
start has only about 1.03 m and was removed because the full robot cannot safely turn in place.
Global and local inflation use `1.45 m`, just above the polygon footprint's `1.438 m`
circumscribed radius, with fast `3.5` cost decay. This enables optimized full-footprint
checks without turning the whole inflation radius into a lethal exclusion zone. Static navigation
follows paths at a nominal
1.6 m/s with a 1.8 m/s output limit, 1.2 m/s² acceleration and 1.5 m/s² braking.
Smac 2D no longer imposes a car-like `0.8 m` turning radius. RPP rotates around the drive axle
before forward travel when the path begins more than `0.35 rad` away.
Cost-regulated controller scaling reduces speed within `0.85 m` of inflated obstacle cost while
preserving the nominal speed in open areas, preventing high-speed corner cutting near walls.
`PositionGoalChecker` ends the action within `0.30 m` of the selected point and ignores final yaw;
this prevents repeated loops around an already reached position.
Smac uses `ALL_DIRECTION` arrival headings, position success is not blocked by the remaining
length of an obsolete terminal loop, and the static-world behavior tree replans only for a changed
goal or an invalid path. This prevents last-moment route replacement and forced turns.
Recovery now guarantees `ComputePathToPose` before every retried `FollowPath`, eliminating the
observed empty-plan loop after costmap clearing or backup. Blind spin recovery is excluded.
The branch is a `SequenceWithMemory`, preventing `ComputePathToPose` from being re-ticked at the
20 Hz control rate while `FollowPath` is still running.
The local controller is Regulated Pure Pursuit with a nominal 2.0 m/s speed, adaptive
0.40..0.80 m lookahead and curvature-based speed reduction. Velocity Smoother applies 1.8 m/s²
linear and symmetric 2.2 rad/s² angular acceleration/deceleration limits. An equal-route upper-corridor comparison
reduced peak path error from 0.106 m to 0.069 m, mean error from 0.055 m to 0.027 m and centerline
crossings from 8 to 0. A corridor-exit turn reached its goal with 0.159 m peak and 0.064 m mean
error; the straight-section requirement of at most 0.10 m is satisfied.
MPPI does not score the local inflation gradient again over the complete asymmetric footprint;
that duplicated clearance cost made valid doorways more expensive than stopping. The globally
inflated Smac path and hard polygon trajectory validator retain collision safety, while stronger
path-follow scoring maintains useful forward motion. A velocity-deadband critic penalizes
ineffective commands below `0.12 m/s` linear or `0.08 rad/s` angular.
The controller uses `SimpleProgressChecker`: only `0.20 m` of real translation within 10 seconds
counts as progress. Rotation or rocking can no longer keep a physically stuck navigation action
alive indefinitely; recovery clears, replans and backs up when needed. Velocity Smoother alone
enforces the physical `1.2 m/s²` linear and `0.8 rad/s²` angular acceleration limits.
The footprint covers the ground-contact chassis and wheel outer edges
(`x=-0.585..0.49 m`, `y=-0.33..0.33 m`); elevated folded-arm links do not create a fictitious
planar exclusion zone. The controller turns in place instead of requiring a Dubins arc.
Local inflation is restored to `0.90 m` with `2.5` decay, preserving usable doorway width while
the trajectory validator continues hard full-footprint collision checks.
Every recovery recomputes `{path}` after clearing or backing up before retrying `FollowPath`, so a
cleared zero-pose path can no longer be sent to the controller.

Remaining manual acceptance checks:

- [ ] Drive right-angle, curved and final-yaw goals on the user's saved map
- [ ] Verify doorway, corridor and furnished-room clearance
- [ ] Navigate between every required room in the static indoor world
- [ ] Inspect oscillation near walls and goals on routes not covered by automation

Expected result: the robot autonomously reaches goals on the saved map when the simulated world
matches that map.

### 13. Obstacle avoidance and navigation safety — implemented

Add perception and response for obstacles that are absent from the saved map. Known static
obstacles remain the responsibility of the global map and costmap from milestone 11.

#### 13.1 Add live obstacle perception

- [x] Add a rolling local costmap with lidar obstacle marking and clearing
- [x] Verify that newly inserted obstacles appear and removed obstacles are cleared
- [x] Retain obstacles outside the lidar view and clear them only after observed free-space evidence
- [x] Tune observation range, persistence and inflation for the robot footprint

#### 13.2 Add avoidance and replanning

- [x] Avoid a newly inserted obstacle when local clearance exists
- [x] Request a new global path when the current route is blocked
- [x] Stop and report failure when no safe route exists
- [x] Resume or accept a new goal after the obstruction is removed
- [x] Test partial and complete blockage of a corridor

#### 13.3 Add a collision-monitor safety layer

- [x] Add independent slowdown and stop zones around the robot
- [x] Route autonomous velocity commands through the collision monitor
- [x] Verify emergency stopping for a close obstacle
- [x] Verify the robot body does not trigger false positive stops
- [x] Cover perception, avoidance, blockage recovery and safety configuration with repeatable tests

Implementation status: `obstacle_navigation.launch.py` adds lidar obstacle layers to both Nav2
costmaps, periodic 1 Hz global replanning and Collision Monitor after Velocity Smoother. Its stop
polygon has priority over the larger 35% slowdown polygon. `obstacle_manager` creates and removes
a parameterized collision box through Gazebo services. A separate map-frame obstacle memory keeps
observations when they leave the lidar view, while a native non-clearable Nav2 costmap plugin writes
them directly into the master global costmap as lethal cells. A remembered region is removed only
after repeated neighbouring rays confirm free space. Global recovery and obstacle-removal services
never erase that memory blindly. The acceptance test inserts a partial corridor obstruction, verifies its
lethal cost and persistence after a detour, then verifies evidence-based removal, safe waiting
behind a complete obstruction and successful goal acceptance after removal. All simulation
tests run in isolated process groups and are forcibly cleaned up on failure or timeout.

Expected result: the robot avoids unexpected obstacles when possible, replans when necessary and
stops safely when no collision-free response exists.

### 14. Physical Gazebo manipulator control

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

Process hygiene is part of acceptance for every roadmap stage: each Gazebo, RViz, SLAM or Nav2
test must end with a host process-table check. Confirmed orphan processes from the completed run
must be stopped with `SIGINT`, then `SIGTERM`, and `SIGKILL` only if graceful shutdown fails. A test
is not complete while one of its simulation or visualization processes remains alive.

These items should follow a concrete navigation or manipulation use case:

- [ ] Named manipulator poses such as `stowed`, `pickup` and `cargo_place`
- [ ] Coordinated multi-joint commands and smoother motion profiles
- [ ] Rear cargo bin/tray design
- [ ] Dynamic boxes or pallets that can be pushed
- [ ] Gripper/object interaction and attachment logic
- [ ] Camera or depth camera near the gripper
- [ ] Contact/bumper sensors
- [ ] Additional apartment-like environment if needed

## Current package structure

```text
robotics_playground_ws/src/
├── learning/                  # ROS 2 concept examples
├── learning_interfaces/       # learning custom interfaces
├── cargo_bot/                 # robot, RViz and control nodes
├── cargo_bot_interfaces/      # manipulator custom interfaces
├── cargo_bot_world/           # Gazebo worlds, models and world builder
└── cargo_bot_navigation/      # SLAM mapping and future Nav2 configuration
```

The RViz-only and Gazebo drive modes intentionally share the `/cmd_vel` interface:

- `cargo_bot/warehouse_in_rviz.launch.py` — visual environment and kinematic movement;
- `cargo_bot_world/gazebo_warehouse.launch.py` — warehouse physics;
- `cargo_bot_world/indoor_rooms.launch.py` — multi-room physics environment.
