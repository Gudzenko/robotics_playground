# ROS 2 Learning Roadmap

## Project overview

Self-contained ROS 2 learning project on Ubuntu 24.04 without physical hardware.  
All code is Python, built with `colcon`, workspace at `robotics_playground_ws/`.

- **ROS 2 version:** Jazzy
- **Package:** `learning` (`ament_python`)
- **Interfaces package:** `learning_interfaces` (`ament_cmake`)
- **Full documentation:** [README.md](README.md)

---

## Completed

### Core ROS 2 concepts (`learning` package)

| Topic | What was built | Where to read |
|---|---|---|
| **Topics** | `status_publisher`, `status_subscriber`, `command_publisher`, `command_subscriber` | README → Topics |
| **Services** | `robot_server` (uptime + reset), `reset_client`, `status_client` | README → Services |
| **Actions** | `count_mission_server` + `count_mission_client` (Fibonacci, cancel support) | README → Actions |
| **Parameters** | `configurable_pub` (runtime param changes), `param_client` | README → Parameters |
| **Launch files** | `topics.launch.py`, `full_system.launch.py` (args, include, LogInfo) | README → Launch files |
| **Lifecycle** | `managed_sensor` — full state machine, publisher created/destroyed on transitions | README → Lifecycle |
| **QoS** | `qos_publisher` + `qos_subscriber` — reliability compatibility, depth/drop demo | README → QoS |
| **Rosbag** | CLI only — record, play, inspect | README → Rosbag |
| **Executors** | `blocking_demo` — SingleThreaded vs MultiThreaded + ReentrantCallbackGroup | README → Executors |
| **Diagnostics** | `robot_monitor` — Battery/Motor/Sensor → `/diagnostics` via `DiagnosticUpdater` | README → Diagnostics |
| **Custom interfaces** | `RobotStatus.msg`, `SetPatrolPoints.srv`, `Patrol.action` + 6 nodes | README → Custom interfaces |

---

## In progress / Next steps

### 1. Cargo Bot visual model (next)

Create a production-style robot model named `cargo_bot` and visualize it in RViz.

The robot is a heavy warehouse cargo platform intended, in the long term, for moving boxes and payloads up to roughly 2 tons. The first version focuses only on the robot's visual model and TF structure. Navigation, apartment/warehouse environment visualization, sensors, manipulator control, and physics are intentionally postponed.

**Current design assumptions:**

- Package name: `cargo_bot`
- Robot/model name: `cargo_bot`
- Robot type: heavy warehouse hybrid platform
- Drive layout: differential drive, two large side drive wheels
- Support wheel: one passive rear caster/support wheel
- Cargo area: rear cargo deck for boxes; rear bin/tray postponed until the cargo area design is clearer
- Future manipulator: mounted on the robot later as a separate module
- Future sensors: lidar, cameras, IMU, and contact sensors may be added later, but are not part of the first visual model

**Why split the model into modules:**

The URDF/Xacro model should be split even if the first version is small. This makes it easier to replace the base, wheels, cargo area, sensors, or manipulator independently later.

Planned initial package structure:

```
robotics_playground_ws/src/cargo_bot/
├── cargo_bot/
│   └── __init__.py
├── launch/
│   └── display.launch.py
├── resource/
│   └── cargo_bot
├── rviz/
│   └── cargo_bot_display.rviz
├── urdf/
│   ├── cargo_bot.urdf.xacro
│   ├── cargo_bot_base.xacro
│   ├── cargo_bot_materials.xacro
│   └── cargo_bot_wheels.xacro
├── package.xml
├── setup.cfg
└── setup.py
```

**Small implementation steps:**

- [x] Create new package `cargo_bot` (`ament_python`) with the planned folder structure
- [x] Add the smallest possible URDF/Xacro model:
  - `base_footprint`
  - `base_link`
  - one simple temporary body box
- [x] Add `display.launch.py` and RViz config early:
  - load `robot_description`
  - start `robot_state_publisher`
  - start `joint_state_publisher_gui`
  - open RViz with RobotModel, TF, and Grid
  - support `visual_mode:=dev` for transparent debug materials and `visual_mode:=prod` for opaque materials
- [x] First visual checkpoint: RViz opens and shows the minimal robot body and TF frames
- [x] Split the temporary model into modules:
  - `cargo_bot_materials.xacro`
  - `cargo_bot_base.xacro`
  - `cargo_bot_wheels.xacro`
  - main `cargo_bot.urdf.xacro`
- [x] Replace the temporary body with the heavy low chassis
- [x] Visual checkpoint: chassis proportions look like a warehouse cargo platform
- [x] Add the top cargo deck
- [x] Visual checkpoint: cargo deck is aligned with the chassis and does not hide TF frames
- [x] Add left and right drive wheels with continuous joints
- [x] Visual checkpoint: wheels sit on the ground plane, rotate around the correct axis, and are symmetric
- [x] Add the rear caster/support wheel
- [x] Visual checkpoint: final first-version robot has a clear 2-drive-wheel + rear-support layout
- [x] Document the package, model structure, and launch command in README

**Expected result:** `ros2 launch cargo_bot display.launch.py` opens RViz with the cargo robot model and TF tree visible.

**Explicitly not included in this step:**

- [ ] No rear cargo bin/tray yet
- [ ] No sensors yet
- [ ] No manipulator yet
- [ ] No `/cmd_vel` movement yet
- [ ] No odometry yet
- [ ] No Gazebo physics yet
- [ ] No apartment/warehouse environment yet
- [ ] No navigation yet

---

### 2. TF + simple RViz movement (after visual model)

Make the robot move in RViz without Gazebo physics. This should be a small kinematic simulation layer used to understand TF, odometry, wheel joints, and `/cmd_vel`.

**What needs to be done:**

- [x] Move shared geometry/kinematics parameters to `config/cargo_bot_geometry.yaml`
- [x] Add a simple differential-drive kinematics node
- [x] Subscribe to `/cmd_vel`
- [x] Publish `odom -> base_footprint`
- [x] Publish `nav_msgs/Odometry` on `/odom`
- [x] Publish wheel joint states so the wheels rotate visually
- [x] Add `drive_in_rviz.launch.py` for movement visualization without `joint_state_publisher_gui`
- [x] Use `teleop_twist_keyboard` or a small custom teleop node for manual control
- [x] Visualize movement and TF in RViz
- [x] Generate/check TF tree via `ros2 run tf2_tools view_frames`
- [x] Document in README

**Expected result:** the robot can be driven around the RViz grid with `/cmd_vel`, while TF, odometry, and wheel animation remain consistent.

---

### 3. Manipulator visual model (later)

Add a separate manipulator module to the robot model. This should stay modular so the manipulator can be replaced or redesigned without rewriting the base platform.

**Long-term manipulator idea:**

- Vertical lift axis
- Rotation around the vertical axis
- Telescoping/extendable arm
- Gripper
- Camera mounted near the gripper
- Purpose: take objects from shelves and place them into the rear cargo bin/tray

**What needs to be done later:**

- [ ] Revisit rear cargo bin/tray design when object placement requirements are clearer
- [x] Add `cargo_bot_manipulator.xacro`
- [x] Add lift joint (`prismatic`)
- [x] Add rotation joint (`revolute` or `continuous`)
- [x] Add telescoping arm joint (`prismatic`)
- [x] Add gripper joints
- [x] Add camera link near the gripper
- [x] Control joints manually through `joint_state_publisher_gui` first
- [x] Document link/joint structure in README

---

### 4. Manipulator control node (later)

Add a dedicated ROS control layer for the manipulator after the visual model is stable.

**Current interface contract:**

- `MoveManipulatorElement.action`: sends one movement command to one manipulator element.
- `CancelManipulatorOperation.srv`: requests cancellation by `operation_id`.
- `GetManipulatorState.srv`: returns the current state of all manipulator elements.
- `ManipulatorElementState.msg`: describes one element state with its name, position, movement flag, operation id, and status.
- The control node now implements the basic command, cancel, state, limit validation, and RViz joint-state flow.

**What needs to be done later:**

- [x] Decide command interface: one Action operation per manipulator element
- [x] Create `cargo_bot_interfaces` with `MoveManipulatorElement.action`
- [x] Create `CancelManipulatorOperation.srv` interface
- [x] Create `GetManipulatorState.srv` interface
- [x] Create `manipulator_control_node` skeleton
- [x] Connect `GetManipulatorState.srv` to `manipulator_control_node` with initial static states
- [x] Move shared manipulator element names and statuses into constants
- [x] Move initial manipulator element state values into defaults
- [x] Add `MoveManipulatorElement.action` server with operation id generation and basic validation
- [x] Load manipulator element limits from `cargo_bot_geometry.yaml`
- [x] Validate command positions against per-element limits
- [x] Update stored element state after a successful command
- [x] Connect `CancelManipulatorOperation.srv` to `manipulator_control_node`
- [x] Add element busy-state check before accepting movement
- [x] Use a reentrant callback group and multithreaded executor for parallel callbacks
- [x] Execute accepted commands for `duration_sec` at the state level
- [x] Allow `CancelManipulatorOperation.srv` to interrupt an active state-level operation
- [x] Publish manipulator joint states from `manipulator_control_node`
- [x] Add RViz launch mode driven by `manipulator_control_node`
- [x] Move non-manipulator passive joint states into a separate publisher
- [x] Add linear interpolation for state-level manipulator movement
- [x] Add commands for lift, rotation, telescoping arm, and gripper
- [x] Generate an `operation_id` for every accepted or rejected command
- [x] Return only `started`, `done`, or `error` statuses
- [x] Allow different elements to move in parallel
- [x] Reject a new command if the same element is already moving
- [x] Add cancel by `operation_id`; a successfully canceled running operation returns `done`
- [x] Add a state query interface for positions, active operations, and last statuses
- [x] Publish joint states from the control node instead of using `joint_state_publisher_gui`
- [x] Add safety limits based on `cargo_bot_geometry.yaml`
- [x] Document usage in README

**Possible refactoring / cleanup:**

- [x] Extract geometry loading helpers from `manipulator_control_node.py`
- [x] Extract manipulator operation state handling into a small dedicated class
- [x] Consider moving shared joint-state publish timing constants into a common module

---

### 5. Manipulator enhancements (later)

Keep these out of the current basic control step until they are needed by a concrete workflow.

**Candidate future improvements:**

- [ ] Add simple named poses, e.g. stowed, pickup, place-to-cargo-deck
- [ ] Add smoother motion profiles instead of linear interpolation
- [ ] Add a higher-level command layer for coordinated multi-element motions
- [ ] Add real gripper/object interaction when physics simulation is introduced

---

### 6. Sensors (later)

Add sensors only when they are needed by the next concrete step. Avoid placeholder links in the first robot model unless a sensor is being implemented.

**Candidate future sensors:**

- [ ] Lidar for mapping/navigation
- [ ] Camera or depth camera on/near the manipulator gripper
- [ ] IMU in the robot base
- [ ] Contact/bumper sensors for simulation
- [ ] Rear or cargo-bin camera if needed for box placement

**Expected approach:** each sensor should be added as a separate Xacro module and documented with its frame name, topic names, and intended use.

---

### 7. Gazebo / physics (later)

Simulate the robot in a physics environment.

**What needs to be done:**

- [ ] Choose simulator: **Gazebo Harmonic** (recommended for Jazzy) or Ignition
- [ ] Add `gz_sim` / `ros_gz_bridge` integration
- [ ] Add differential drive plugin to the robot model (`ros2_control` or Gazebo diff-drive plugin)
- [ ] Add collision and inertial properties to robot links
- [ ] Revisit visual/collision geometry and remove collision overlaps between chassis, wheels, cargo deck, and rear support caster
- [ ] Create a simple world file (flat ground + walls/warehouse area)
- [ ] Launch file that starts Gazebo + spawns the robot + starts `robot_state_publisher`
- [ ] Verify that velocity commands (`/cmd_vel`) move the robot and odometry (`/odom`) is published
- [ ] Document in README

---

### 8. Warehouse environment visualization

Create a simple RViz-only warehouse scene around the robot. This step is for visual context and scale checks only; it does not add Gazebo physics, collision handling, mapping, or navigation.

**Planned approach:**

- [x] Choose first environment type: warehouse
- [x] Choose first visualization approach: RViz `MarkerArray`
- [x] Create a separate `warehouse_scene_publisher` node
- [x] Publish a floor, simple boundary walls, shelf blocks, and a loading/drop-off area
  - [x] Publish the first floor marker
  - [x] Publish simple boundary wall markers
  - [x] Publish first shelf block markers
  - [x] Split warehouse scene marker factories by object type
  - [x] Publish the first loading/drop-off zone marker
  - [x] Publish first box markers
- [x] Keep dimensions realistic enough for later mapping/navigation experiments
- [x] Add a launch file that starts the robot, warehouse scene, and RViz
- [x] Verify that the robot can be driven visually through the warehouse scene
- [x] Document launch commands and model structure

**Current limitation:** this RViz scene is visual only. It does not prevent the robot from driving through walls, shelves, boxes, or zones. Collision handling belongs to future Gazebo/physics or navigation/costmap steps.

**Future variants:**

- [ ] Add an apartment-like environment later if needed
- [ ] Move the warehouse scene into Gazebo when physics simulation starts

---

### 9. Nav2 (much later)

Autonomous navigation: map, planner, costmap.

**What needs to be done:**

- [ ] Install Nav2 (`ros-jazzy-navigation2`, `ros-jazzy-nav2-bringup`)
- [ ] Add a lidar plugin to the Gazebo robot model (publishes `sensor_msgs/LaserScan`)
- [ ] Run SLAM Toolbox to build a map of the Gazebo world
- [ ] Save the map, configure Nav2 with it
- [ ] Send navigation goals via RViz `Nav2 Goal` tool or `NavigateToPose` action
- [ ] Document in README

---

## Package structure (current)

```
robotics_playground_ws/src/
├── learning/                        # main educational package (ament_python)
│   ├── learning/
│   │   ├── constants.py
│   │   ├── topics/
│   │   ├── services/
│   │   ├── actions/
│   │   ├── parameters/
│   │   ├── lifecycle/
│   │   ├── qos/
│   │   ├── executors/
│   │   ├── diagnostics/
│   │   └── custom_interfaces/
│   └── launch/
└── learning_interfaces/             # custom msg/srv/action types (ament_cmake)
    ├── msg/RobotStatus.msg
    ├── srv/SetPatrolPoints.srv
    └── action/Patrol.action
```

**To be added:**
```
└── cargo_bot/                       # robot model, URDF/Xacro, RViz config, display launch
```
