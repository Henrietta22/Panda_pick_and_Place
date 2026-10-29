import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from moveit_msgs.msg import CollisionObject, AttachedCollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose
import time

class PandaPickAndPlace(Node):
    def __init__(self):
        super().__init__('panda_pick_and_place')
        self.arm_pub = self.create_publisher(JointTrajectory, '/panda_arm_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/panda_hand_controller/joint_trajectory', 10)
        self.collision_pub = self.create_publisher(CollisionObject, '/collision_object', 10)
        self.attached_pub = self.create_publisher(AttachedCollisionObject, '/attached_collision_object', 10)

        time.sleep(1.0)
        self.setup_scene()
        self.run_sequence()

    def create_box(self, name, x, y, z, size_x, size_y, size_z):
        obj = CollisionObject()
        obj.header.frame_id = 'world'
        obj.id = name
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [float(size_x), float(size_y), float(size_z)]
        pose = Pose()
        pose.position.x = float(x)
        pose.position.y = float(y)
        pose.position.z = float(z)
        pose.orientation.w = 1.0
        obj.primitives.append(box)
        obj.primitive_poses.append(pose)
        obj.operation = CollisionObject.ADD
        return obj

    def setup_scene(self):
        self.get_logger().info('Spawning tables and green target box in RViz scene...')
        # Table 1 (Pick Station)
        table1 = self.create_box('pick_table', 0.45, 0.25, 0.2, 0.3, 0.3, 0.4)
        # Table 2 (Place Station)
        table2 = self.create_box('place_table', 0.15, -0.45, 0.2, 0.3, 0.3, 0.4)
        # Target Cargo Workpiece
        box = self.create_box('target_box', 0.45, 0.25, 0.45, 0.05, 0.05, 0.10)

        for _ in range(3):
            self.collision_pub.publish(table1)
            self.collision_pub.publish(table2)
            self.collision_pub.publish(box)
            time.sleep(0.1)

    def attach_box_to_gripper(self, attach=True):
        att = AttachedCollisionObject()
        att.link_name = 'panda_hand'
        att.object.header.frame_id = 'panda_hand'
        att.object.id = 'target_box'
        att.touch_links = ['panda_leftfinger', 'panda_rightfinger', 'panda_hand']

        if attach:
            # Remove from world collision, attach to hand
            att.object.operation = CollisionObject.ADD
            box = SolidPrimitive()
            box.type = SolidPrimitive.BOX
            box.dimensions = [0.05, 0.05, 0.10]
            pose = Pose()
            pose.position.z = 0.08
            pose.orientation.w = 1.0
            att.object.primitives.append(box)
            att.object.primitive_poses.append(pose)
        else:
            # Detach
            att.object.operation = CollisionObject.REMOVE

        self.attached_pub.publish(att)

    def move_arm(self, positions, duration=2.0):
        msg = JointTrajectory()
        msg.joint_names = [f'panda_joint{i}' for i in range(1, 8)]
        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in positions]
        pt.time_from_start.sec = int(duration)
        pt.time_from_start.nanosec = int((duration % 1) * 1e9)
        msg.points.append(pt)
        self.arm_pub.publish(msg)
        time.sleep(duration + 0.3)

    def move_gripper(self, width, duration=0.8):
        msg = JointTrajectory()
        msg.joint_names = ['panda_finger_joint1', 'panda_finger_joint2']
        pt = JointTrajectoryPoint()
        pt.positions = [float(width / 2.0), float(width / 2.0)]
        pt.time_from_start.sec = int(duration)
        pt.time_from_start.nanosec = int((duration % 1) * 1e9)
        msg.points.append(pt)
        self.gripper_pub.publish(msg)
        time.sleep(duration + 0.2)

    def run_sequence(self):
        self.get_logger().info('=== Starting Full Visual Pick-and-Place ===')

        # 1. Open gripper & Move to Ready Home
        self.get_logger().info('1. Readying arm and opening fingers...')
        self.move_gripper(0.08)
        self.move_arm([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785], duration=2.0)

        # 2. Pre-grasp above workpiece
        self.get_logger().info('2. Pre-grasp position over Station A...')
        self.move_arm([0.45, -0.5, 0.0, -2.1, 0.0, 1.6, 1.2], duration=2.0)

        # 3. Descend onto workpiece
        self.get_logger().info('3. Descending onto target box...')
        self.move_arm([0.45, -0.25, 0.0, -1.9, 0.0, 1.65, 1.2], duration=1.5)

        # 4. Close fingers & attach object to gripper link
        self.get_logger().info('4. Grasping box and locking to gripper...')
        self.move_gripper(0.03)
        self.attach_box_to_gripper(attach=True)
        time.sleep(0.5)

        # 5. Lift box
        self.get_logger().info('5. Lifting box into the air...')
        self.move_arm([0.45, -0.7, 0.0, -2.3, 0.0, 1.6, 1.2], duration=2.0)

        # 6. Transfer across to Place Station
        self.get_logger().info('6. Carrying box to Station B...')
        self.move_arm([-0.8, -0.5, 0.0, -2.1, 0.0, 1.6, -0.1], duration=3.0)

        # 7. Lower box over Place Station
        self.get_logger().info('7. Lowering box onto Station B table...')
        self.move_arm([-0.8, -0.25, 0.0, -1.9, 0.0, 1.65, -0.1], duration=1.5)

        # 8. Release box & open gripper
        self.get_logger().info('8. Releasing box...')
        self.attach_box_to_gripper(attach=False)
        # Place new static box at destination
        placed_box = self.create_box('target_box_placed', 0.15, -0.45, 0.45, 0.05, 0.05, 0.10)
        self.collision_pub.publish(placed_box)
        self.move_gripper(0.08)

        # 9. Retract and return Home
        self.get_logger().info('9. Returning to Home pose...')
        self.move_arm([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785], duration=2.5)

        self.get_logger().info('=== Pick-and-Place Demonstration Complete! ===')

def main():
    rclpy.init()
    node = PandaPickAndPlace()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
