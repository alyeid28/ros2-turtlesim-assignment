# ROS 2 Turtlesim Assignment

A ROS 2 Humble project that demonstrates custom ROS interfaces, action servers, services, turtle pose control, square drawing, and runtime speed configuration.

## Team Members

- Aly Eid — ID: 9561
- Abdullah Haitham — ID: 9678
- Yahia Mostafa — ID: 9475
- Mohamed Tarek — ID: 9607

## Project Structure

### `turtle_interfaces`

Contains the custom ROS 2 interfaces used by the project:

- `msg/TargetPose.msg` — Defines the target position (`x`, `y`) and orientation (`yaw`).
- `action/GoToPose.action` — Defines the goal, result, and feedback for turtle movement.
- `srv/SetSpeedLimits.srv` — Defines the service request and response for configuring speed limits.

### `turtle_control`

Contains the Python nodes and launch file:

- `go_to_pose_server.py` — Action server for moving the turtle to a target pose.
- `square_action_server.py` — Action server for square drawing.
- `reset_service.py` — Service for clearing the drawing and resetting the turtle.
- `set_speed_service.py` — Service for changing speed limits.
- `launch/turtle_system.launch.py` — Launches Turtlesim and the project nodes.

## Requirements

- Ubuntu
- ROS 2 Humble
- Python 3
- Turtlesim

## Build

Open a terminal and run:

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2_ws
colcon build --packages-up-to turtle_control
source ~/ros2_ws/install/setup.bash
```

## Launch the Project

The launch file starts Turtlesim, both action servers, and the reset and speed-limit services.

```bash
ros2 launch turtle_control turtle_system.launch.py
```

## Usage

Run the following commands in a separate terminal after sourcing the ROS 2 and workspace environments:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

### Move to a Target Pose

Send a target position and orientation to the `go_to_pose` action server:

```bash
ros2 action send_goal /go_to_pose turtle_interfaces/action/GoToPose "{target: {x: 7.0, y: 7.0, yaw: 0.0}}" --feedback
```

The target coordinates are in the Turtlesim window, and `yaw` specifies the target orientation in radians.

### Draw a Square

Send a goal to the square drawing action server:

```bash
ros2 action send_goal /draw_square turtle_interfaces/action/GoToPose "{}" --feedback
```

### Reset the Turtle

Clear the drawing and request a reset to the initial pose:

```bash
ros2 service call /reset_turtle std_srvs/srv/Empty "{}"
```

### Change Speed Limits

Set the maximum linear and angular speeds:

```bash
ros2 service call /set_speed_limits turtle_interfaces/srv/SetSpeedLimits "{max_linear_speed: 1.0, max_angular_speed: 1.5}"
```

The values are examples; use positive values appropriate for your test.

## Rosbag Recording and Playback

ROS 2 bags can record and replay topic data for testing and analysis.

To record turtle velocity commands and pose updates:

```bash
ros2 bag record /turtle1/cmd_vel /turtle1/pose
```

Stop recording with `Ctrl+C`. ROS 2 creates a bag directory in the current working directory.

To replay a recording, replace `<bag_directory>` with the name of the directory created during recording:

```bash
ros2 bag play <bag_directory>
```

## Notes

- Source the ROS 2 Humble environment and workspace setup file in each new terminal before running project commands.
- The launch file configures the movement server with default maximum linear and angular speeds of `2.0`.
