#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import (
    ReentrantCallbackGroup,
    MutuallyExclusiveCallbackGroup
)
from rclpy.executors import MultiThreadedExecutor

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose

from turtle_interfaces.action import GoToPose


def normalize_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class GoToPoseServer(Node):

    def __init__(self):
        super().__init__('go_to_pose_server')

        self.declare_parameter('max_linear_speed', 2.0)
        self.declare_parameter('max_angular_speed', 2.0)

        self.declare_parameter('linear_gain', 1.0)
        self.declare_parameter('angular_gain', 4.0)

        self.pose = None

        self.pose_group = ReentrantCallbackGroup()
        self.action_group = MutuallyExclusiveCallbackGroup()

        self.pose_subscriber = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10,
            callback_group=self.pose_group
        )

        self.velocity_publisher = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        self.action_server = ActionServer(
            self,
            GoToPose,
            '/go_to_pose',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.action_group
        )

        self.get_logger().info('goToPose action server is ready.')

    def pose_callback(self, msg):
        self.pose = msg

    def goal_callback(self, request):
        target = request.target

        if not all(math.isfinite(v) for v in
                   (target.x, target.y, target.yaw)):
            self.get_logger().warning('Rejected non-finite goal.')
            return GoalResponse.REJECT

        if not (0.0 <= target.x <= 11.0 and
                0.0 <= target.y <= 11.0):
            self.get_logger().warning(
                'Rejected goal outside the turtlesim window.'
            )
            return GoalResponse.REJECT

        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        return CancelResponse.ACCEPT

    def stop_turtle(self):
        self.velocity_publisher.publish(Twist())

    def execute_callback(self, goal_handle):
        target = goal_handle.request.target

        result = GoToPose.Result()
        feedback = GoToPose.Feedback()

        position_tolerance = 0.04
        angle_tolerance = 0.025
        heading_tolerance = 0.04

        try:
            while rclpy.ok():

                if goal_handle.is_cancel_requested:
                    self.stop_turtle()
                    goal_handle.canceled()
                    result.success = False
                    result.message = 'Goal canceled.'
                    return result

                if self.pose is None:
                    time.sleep(0.05)
                    continue

                dx = target.x - self.pose.x
                dy = target.y - self.pose.y
                distance = math.hypot(dx, dy)

                feedback.distance_remaining = float(distance)
                goal_handle.publish_feedback(feedback)

                max_linear = max(
                    0.05,
                    float(self.get_parameter('max_linear_speed').value)
                )
                max_angular = max(
                    0.05,
                    float(self.get_parameter('max_angular_speed').value)
                )

                linear_gain = float(
                    self.get_parameter('linear_gain').value
                )
                angular_gain = float(
                    self.get_parameter('angular_gain').value
                )

                cmd = Twist()

                if distance > position_tolerance:

                    desired_heading = math.atan2(dy, dx)
                    heading_error = normalize_angle(
                        desired_heading - self.pose.theta
                    )

                    # Turn in place until aligned with the target.
                    if abs(heading_error) > heading_tolerance:
                        cmd.angular.z = clamp(
                            angular_gain * heading_error,
                            -max_angular,
                            max_angular
                        )

                    # Once aligned, travel straight toward the target.
                    else:
                        cmd.linear.x = clamp(
                            linear_gain * distance,
                            0.0,
                            max_linear
                        )

                else:
                    # Position reached: rotate to the requested final yaw.
                    yaw_error = normalize_angle(
                        target.yaw - self.pose.theta
                    )

                    if abs(yaw_error) <= angle_tolerance:
                        self.stop_turtle()
                        result.success = True
                        result.message = 'Target pose reached.'
                        goal_handle.succeed()

                        self.get_logger().info(
                            f'Reached target: x={target.x:.2f}, '
                            f'y={target.y:.2f}, yaw={target.yaw:.2f}'
                        )
                        return result

                    cmd.angular.z = clamp(
                        angular_gain * yaw_error,
                        -max_angular,
                        max_angular
                    )

                self.velocity_publisher.publish(cmd)
                time.sleep(0.03)

            self.stop_turtle()
            result.success = False
            result.message = 'ROS 2 stopped before reaching the target.'

            if goal_handle.is_active:
                goal_handle.abort()

            return result

        except Exception as exc:
            self.stop_turtle()

            result.success = False
            result.message = str(exc)

            self.get_logger().error(f'Movement failed: {exc}')

            if goal_handle.is_active:
                goal_handle.abort()

            return result


def main(args=None):
    rclpy.init(args=args)
    node = GoToPoseServer()

    executor = MultiThreadedExecutor(num_threads=3)
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.stop_turtle()
        except Exception:
            pass

        executor.shutdown()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
