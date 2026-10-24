#!/usr/bin/env python3

import math
import threading

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter as ParameterMsg
from rcl_interfaces.msg import ParameterValue
from rcl_interfaces.msg import ParameterType

from turtle_interfaces.srv import SetSpeedLimits


class SetSpeedService(Node):

    def __init__(self):
        super().__init__('set_speed_service')

        self.callback_group = ReentrantCallbackGroup()

        self.parameter_client = self.create_client(
            SetParameters,
            '/go_to_pose_server/set_parameters',
            callback_group=self.callback_group
        )

        self.set_speed_server = self.create_service(
            SetSpeedLimits,
            '/set_speed_limits',
            self.set_speed_callback,
            callback_group=self.callback_group
        )

        self.get_logger().info(
            'Speed limit service ready at /set_speed_limits.'
        )

    def set_speed_callback(self, request, response):
        linear = float(request.max_linear_speed)
        angular = float(request.max_angular_speed)

        if (
            not math.isfinite(linear)
            or not math.isfinite(angular)
            or linear <= 0.0
            or angular <= 0.0
        ):
            response.success = False
            response.message = (
                'Speed limits must be finite positive numbers.'
            )
            return response

        if not self.parameter_client.wait_for_service(timeout_sec=3.0):
            response.success = False
            response.message = (
                'Cannot find /go_to_pose_server/set_parameters. '
                'Check that go_to_pose_server is running.'
            )
            return response

        parameters = [
            ParameterMsg(
                name='max_linear_speed',
                value=ParameterValue(
                    type=ParameterType.PARAMETER_DOUBLE,
                    double_value=linear
                )
            ),
            ParameterMsg(
                name='max_angular_speed',
                value=ParameterValue(
                    type=ParameterType.PARAMETER_DOUBLE,
                    double_value=angular
                )
            )
        ]

        completed = threading.Event()
        outcome = {'result': None, 'error': None}

        future = self.parameter_client.call_async(
            SetParameters.Request(parameters=parameters)
        )

        def on_complete(future):
            try:
                outcome['result'] = future.result()
            except Exception as exc:
                outcome['error'] = str(exc)
            finally:
                completed.set()

        future.add_done_callback(on_complete)

        if not completed.wait(timeout=5.0):
            response.success = False
            response.message = 'Timed out updating speed limits.'
            return response

        if outcome['error'] is not None:
            response.success = False
            response.message = outcome['error']
            return response

        results = outcome['result']

        if results is None or not all(
            item.successful for item in results.results
        ):
            response.success = False
            response.message = 'The movement server rejected the limits.'
            return response

        response.success = True
        response.message = (
            f'Speed limits updated: linear={linear:.2f}, '
            f'angular={angular:.2f}.'
        )

        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = SetSpeedService()

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
