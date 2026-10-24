from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        # Start TurtleSim.
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
            output='screen'
        ),

        # Start the goToPose action server.
        Node(
            package='turtle_control',
            executable='go_to_pose_server',
            name='go_to_pose_server',
            output='screen',
            parameters=[{
                'max_linear_speed': 2.0,
                'max_angular_speed': 2.0
            }]
        ),

        # Start the square action server.
        Node(
            package='turtle_control',
            executable='square_action_server',
            name='square_action_server',
            output='screen'
        ),

        # Start the reset service.
        Node(
            package='turtle_control',
            executable='reset_service',
            name='reset_service',
            output='screen'
        ),

        # Start the speed-limit service.
        Node(
            package='turtle_control',
            executable='set_speed_service',
            name='set_speed_service',
            output='screen'
        ),

    ])
