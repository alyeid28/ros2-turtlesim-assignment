# ROS 2 Turtlesim Assignment

A ROS 2 Humble project demonstrating custom interfaces, action servers, services, turtle movement control, square drawing, and rosbag recording/playback.

## Team Members

- Aly Eid — ID: 9561
- Abdullah Haitham — ID: 9678
- Yahia Mostafa — ID: 9475

## Packages

### turtle_interfaces
- TargetPose.msg: Target position and orientation.
- GoToPose.action: Turtle movement action.
- SetSpeedLimits.srv: Runtime speed-limit configuration.

### turtle_control
- GoToPose action server.
- Turtle reset service.
- Square drawing action server.
- Speed-limit service.

## Requirements

- Ubuntu
- ROS 2 Humble
- Python 3
- Turtlesim

## Build

    source /opt/ros/humble/setup.bash
    cd ~/ros2_ws
    colcon build --packages-up-to turtle_control
    source ~/ros2_ws/install/setup.bash

## Launch

    ros2 launch turtle_control turtle_system.launch.py

## Reset the Turtle

    ros2 service call /reset_turtle std_srvs/srv/Empty "{}"

## Change Speed Limits

    ros2 service call /set_speed_limits turtle_interfaces/srv/SetSpeedLimits "{max_linear_speed: 1.0, max_angular_speed: 1.5}"

## Move to a Target Pose

    ros2 action send_goal /go_to_pose turtle_interfaces/action/GoToPose "{target: {x: 7.0, y: 7.0, yaw: 0.0}}" --feedback

## Draw a Square

    ros2 action send_goal /draw_square turtle_interfaces/action/GoToPose "{}" --feedback

## Rosbag

The project was tested with rosbag recording and playback using:

- /turtle1/cmd_vel
- /turtle1/pose
