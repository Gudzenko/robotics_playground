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
SLAM, global map localization and autonomous navigation are not implemented yet. Lidar, IMU,
encoder odometry, deterministic noise/source substitution and EKF local odometry are implemented
and form the verified navigation-sensor baseline.

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

### 9. Navigation sensor foundation — next

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
ticks per revolution, integrates exact differential-drive increments using the shared `0.23 m`
wheel radius and `1.16 m` separation, and publishes `/wheel/odometry` without TF. The ready-made
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
forward velocity and yaw rate with IMU yaw rate, publishing `/odometry/filtered` and the sole ROS
`odom -> base_footprint` transform. Gazebo DiffDrive TF moved to `/ground_truth/tf` and is no longer
bridged to `/tf`, while `/ground_truth/odometry` remains available for comparison. Wheel messages
now carry explicit positive pose/twist covariance. Automated isolated Gazebo routes cover both
ideal and seeded `realistic` profiles, verify finite continuous output, and bound wheel/filtered
position error against simulator truth to `0.25 m`/`0.5 m` for the respective short routes. The
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
operation, seeded noise profiles and separate simulator ground truth.

Status: complete. The final build and test run reports 130 tests with 0 errors, 0 failures and
3 skipped lint copyright checks. Headless launch tests cover the warehouse in `ideal` and seeded
`realistic` modes and the indoor world in `ideal` mode. On the short warehouse routes, final
position error versus Gazebo truth was 0.0012 m (wheel) and 0.0237 m (EKF) for `ideal`, and
0.0118 m (wheel) and 0.0136 m (EKF) for seeded `realistic`. RViz verification confirms lidar
returns and the separate wheel, EKF and ground-truth paths. Public sensor interfaces remain stable,
so SLAM Toolbox can consume `/scan`, `/odometry/filtered` and the existing TF tree without changing
the sensor-source architecture.

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
