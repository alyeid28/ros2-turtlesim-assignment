#!/usr/bin/env python3

import threading

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from std_srvs.srv import Empty
from turtlesim.srv import TeleportAbsolute, SetPen


class ResetService(Node):

    def __init__(self):
        super().__init__('reset_service')

        self.callback_group = ReentrantCallbackGroup()

        self.clear_client = self.create_client(
            Empty,
            '/clear',
            callback_group=self.callback_group
        )

        self.teleport_client = self.create_client(
            TeleportAbsolute,
            '/turtle1/teleport_absolute',
            callback_group=self.callback_group
        )

        self.pen_client = self.create_client(
            SetPen,
            '/turtle1/set_pen',
            callback_group=self.callback_group
        )

        self.reset_server = self.create_service(
            Empty,
            '/reset_turtle',
            self.reset_callback,
            callback_group=self.callback_group
        )

        self.get_logger().info('Reset service is ready.')

    def call_service(self, client, request):
        if not client.wait_for_service(timeout_sec=3.0):
            self.get_logger().error(
                f'Service {client.srv_name} is unavailable.'
            )
            return False

        completed = threading.Event()
        result = {'success': False}

        future = client.call_async(request)

        def done_callback(future):
            try:
                result['success'] = future.result() is not None
            except Exception as exc:
                self.get_logger().error(
                    f'Service call failed: {exc}'
                )
            finally:
                completed.set()

        future.add_done_callback(done_callback)

        if not completed.wait(timeout=5.0):
            self.get_logger().error(
                f'Timeout calling {client.srv_name}.'
            )
            return False

        return result['success']

    def reset_callback(self, request, response):
        del request

        # Disable the pen before teleporting.
        pen_off = SetPen.Request()
        pen_off.r = 0
        pen_off.g = 0
        pen_off.b = 0
        pen_off.width = 1
        pen_off.off = 1

        if not self.call_service(self.pen_client, pen_off):
            self.get_logger().error('Could not disable turtle pen.')
            return response

        # Clear the drawing.
        if not self.call_service(self.clear_client, Empty.Request()):
            self.get_logger().error('Could not clear the screen.')
            return response

        # Return the turtle to its initial position and orientation.
        teleport = TeleportAbsolute.Request()
        teleport.x = 5.544
        teleport.y = 5.544
        teleport.theta = 0.0

        if not self.call_service(self.teleport_client, teleport):
            self.get_logger().error('Could not teleport turtle.')
            return response

        # Re-enable the pen.
        pen_on = SetPen.Request()
        pen_on.r = 255
        pen_on.g = 255
        pen_on.b = 255
        pen_on.width = 2
        pen_on.off = 0

        if not self.call_service(self.pen_client, pen_on):
            self.get_logger().error('Could not re-enable turtle pen.')
            return response

        self.get_logger().info('Turtle reset successfully.')
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ResetService()

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
