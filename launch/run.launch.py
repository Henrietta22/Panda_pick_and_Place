from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    moveit_config_dir = get_package_share_directory("moveit_resources_panda_moveit_config")
    demo_launch = os.path.join(moveit_config_dir, "launch", "demo.launch.py")

    moveit_demo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(demo_launch)
    )

    runner_node = TimerAction(
        period=4.0,
        actions=[
            Node(
                package="panda_pick_and_place",
                executable="pick_and_place_node",
                output="screen"
            )
        ]
    )

    return LaunchDescription([moveit_demo, runner_node])
