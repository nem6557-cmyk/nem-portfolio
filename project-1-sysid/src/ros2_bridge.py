"""
ros2_bridge.py
==============
A minimal ROS2 (rclpy) node that runs the MuJoCo arm as a simulation server:

    subscribes  /arm/torque_command   std_msgs/Float64MultiArray   (3 torques)
    publishes   /joint_states         sensor_msgs/JointState       (q, qd, tau)
    publishes   /clock                rosgraph_msgs/Clock          (sim time)

This is the seam where a MuJoCo model plugs into a ROS2 control / perception /
planning stack: any node that speaks JointState and sends torque commands can
drive this arm without knowing it is simulated. Swapping the identified
parameters from Project 1 into the model makes the simulated joint states match
the real arm, so controllers can be tuned in sim before touching hardware.

NOTE ON RUNNING THIS
--------------------
ROS2 is not installed in the authoring sandbox, so this file is provided as a
ready-to-run node rather than something exercised in CI here. On a machine with
ROS2 Humble and `mujoco` installed:

    # terminal 1
    source /opt/ros/humble/setup.bash
    python3 ros2_bridge.py --model ../models/arm3.xml

    # terminal 2, drive it open loop for a quick check
    ros2 topic pub /arm/torque_command std_msgs/Float64MultiArray \
        "{data: [0.0, -2.0, 1.0]}" -r 100
    ros2 topic echo /joint_states

The node uses sim-time semantics: it advances MuJoCo in a wall-clock timer and
republishes the sim clock, which keeps downstream time-stamped data consistent.
"""

from __future__ import annotations

import argparse
import threading

import numpy as np
import mujoco

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState
    from std_msgs.msg import Float64MultiArray
    from rosgraph_msgs.msg import Clock
    _HAVE_ROS = True
except ImportError:
    _HAVE_ROS = False


if _HAVE_ROS:

    class MujocoArmBridge(Node):
        def __init__(self, model_path: str, realtime: float = 1.0):
            super().__init__("mujoco_arm_bridge")
            self.model = mujoco.MjModel.from_xml_path(model_path)
            self.data = mujoco.MjData(self.model)
            self.nu = self.model.nu
            self.joint_names = [
                mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, i)
                for i in range(self.model.njnt)
            ]
            self._cmd = np.zeros(self.nu)
            self._lock = threading.Lock()

            self.cmd_sub = self.create_subscription(
                Float64MultiArray, "/arm/torque_command", self._on_cmd, 10)
            self.js_pub = self.create_publisher(JointState, "/joint_states", 10)
            self.clock_pub = self.create_publisher(Clock, "/clock", 10)

            self.dt = float(self.model.opt.timestep)
            period = self.dt / max(realtime, 1e-6)
            self.timer = self.create_timer(period, self._on_step)
            self.get_logger().info(
                f"MuJoCo arm bridge up: {self.nu} actuators, dt={self.dt:.4f}s")

        def _on_cmd(self, msg: Float64MultiArray) -> None:
            vals = np.asarray(msg.data, dtype=float)
            if vals.size == self.nu:
                with self._lock:
                    self._cmd = vals
            else:
                self.get_logger().warn(
                    f"ignoring command of size {vals.size}, expected {self.nu}")

        def _on_step(self) -> None:
            with self._lock:
                self.data.ctrl[:] = self._cmd
            mujoco.mj_step(self.model, self.data)
            self._publish()

        def _publish(self) -> None:
            now = self.data.time
            sec = int(now)
            nanosec = int((now - sec) * 1e9)

            clk = Clock()
            clk.clock.sec = sec
            clk.clock.nanosec = nanosec
            self.clock_pub.publish(clk)

            js = JointState()
            js.header.stamp.sec = sec
            js.header.stamp.nanosec = nanosec
            js.name = [n for n in self.joint_names if n]
            js.position = self.data.qpos.tolist()
            js.velocity = self.data.qvel.tolist()
            js.effort = self.data.qfrc_actuator.tolist()
            self.js_pub.publish(js)


def main() -> None:
    ap = argparse.ArgumentParser(description="MuJoCo arm ROS2 bridge")
    ap.add_argument("--model", default="../models/arm3.xml")
    ap.add_argument("--realtime", type=float, default=1.0,
                    help="1.0 = real time, >1 faster, <1 slower")
    args = ap.parse_args()

    if not _HAVE_ROS:
        raise SystemExit(
            "rclpy not found. Source a ROS2 install (e.g. "
            "'source /opt/ros/humble/setup.bash') and rerun. See the module "
            "docstring for the full run recipe.")

    rclpy.init()
    node = MujocoArmBridge(args.model, realtime=args.realtime)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
