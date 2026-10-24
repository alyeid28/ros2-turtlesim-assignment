#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from turtlesim.msg import Pose
from turtle_interfaces.action import GoToPose
from turtle_interfaces.msg import TargetPose


class SquareActionServer(Node):

    def __init__(self):
        super().__init__('square_action_server')

        self.declare_parameter('side_length', 2.0)
        self.pose = None

        self.callback_group = ReentrantCallbackGroup()

        self.pose_subscriber = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10,
            callback_group=self.callback_group
        )

        self.action_client = ActionClient(
            self,
            GoToPose,
            '/go_to_pose',
            callback_group=self.callback_group
        )

        self.action_server = ActionServer(
            self,
            GoToPose,
            '/draw_square',
            execute_callback=self.execute_callback,
            callback_group=self.callback_group
        )

        self.get_logger().info('Square action server is ready.')

    def pose_callback(self, msg):
        self.pose = msg

    async def execute_callback(self, goal_handle):
        result = GoToPose.Result()

        # Wait for the movement action server.
        if not self.action_client.wait_for_server(timeout_sec=5.0):
            result.success = False
            result.message = 'go_to_pose action server is unavailable.'
            goal_handle.abort()
            return result

        if self.pose is None:
            result.success = False
            result.message = 'Turtle pose is not available.'
            goal_handle.abort()
            return result

        side = float(self.get_parameter('side_length').value)

        if not math.isfinite(side) or not 0.5 <= side <= 3.0:
            result.success = False
            result.message = 'Side length must be between 0.5 and 3.0.'
            goal_handle.abort()
            return result

        # Start at the turtle's current position.
        start_x = float(self.pose.x)
        start_y = float(self.pose.y)

        # Keep the entire square inside the turtlesim window.
        margin = 0.5

        if (start_x + side > 11.0 - margin or
                start_y + side > 11.0 - margin):
            result.success = False
            result.message = (
                'Not enough space above and to the right. '
                'Reset the turtle and try again.'
            )
            goal_handle.abort()
            return result

        # Four corners, requiring exactly four goToPose calls.
        targets = [
            TargetPose(
                x=start_x + side,
                y=start_y,
                yaw=0.0
            ),
            TargetPose(
                x=start_x + side,
                y=start_y + side,
                yaw=math.pi / 2
            ),
            TargetPose(
                x=start_x,
                y=start_y + side,
                yaw=math.pi
            ),
            TargetPose(
                x=start_x,
                y=start_y,
                yaw=-math.pi / 2
            ),
        ]

        for index, target in enumerate(targets, start=1):

            if goal_handle.is_cancel_requested:
                result.success = False
                result.message = 'Square drawing canceled.'
                goal_handle.canceled()
                return result

            self.get_logger().info(
                f'Moving to corner {index}/4: '
                f'x={target.x:.2f}, y={target.y:.2f}'
            )

            goal = GoToPose.Goal()
            goal.target = target

            # Call goToPose once for this corner.
            send_future = self.action_client.send_goal_async(goal)
            goal_response = await send_future

            if not goal_response.accepted:
                result.success = False
                result.message = f'Corner {index} goal was rejected.'
                goal_handle.abort()
                return result

            movement_result = await goal_response.get_result_async()

            if not movement_result.result.success:
                result.success = False
                result.message = (
                    f'Movement to corner {index} failed: '
                    f'{movement_result.result.message}'
                )
                goal_handle.abort()
                return result

            feedback = GoToPose.Feedback()
            feedback.distance_remaining = float(4 - index)
            goal_handle.publish_feedback(feedback)

        result.success = True
        result.message = (
            'Square completed using exactly four goToPose calls.'
        )

        goal_handle.succeed()
        self.get_logger().info(result.message)

        return result


def main(args=None):
    rclpy.init(args=args)

    node = SquareActionServer()
    executor = MultiThreadedExecutor(num_threads=3)
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
