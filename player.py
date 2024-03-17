from dataclasses import dataclass
from typing import Iterable

import pyray as rl
from pyray import Vector3, Camera3D, KeyboardKey
from system import Planet

from utils import Quat, vec3_zero

@dataclass
class Player:
    pos: Vector3
    vel: Vector3
    camera: Camera3D
    rotation: Quat
    target_rotation: Quat

    def update(self, dt: float):
        """Update camera view angle and speed with inputs, and integrate position over speed"""
        mouse_speed = 0.005
        roll_speed = 0.01
        move_speed = 0.2

        # change view angles
        rot_matrix = rl.quaternion_to_matrix(self.rotation)

        forward = rl.vector3_transform(Vector3(0, 0, -1), rot_matrix)
        up = rl.vector3_transform(Vector3(0, 1, 0), rot_matrix)
        right = rl.vector3_transform(Vector3(1, 0, 0), rot_matrix)

        d = rl.get_mouse_delta()
        yaw = rl.quaternion_from_axis_angle(up, -d.x*mouse_speed)
        pitch = rl.quaternion_from_axis_angle(right, -d.y*mouse_speed)
        roll = rl.quaternion_from_axis_angle(forward, roll_speed*(float(rl.is_key_down(KeyboardKey.KEY_E))-float(rl.is_key_down(KeyboardKey.KEY_Q))))

        rot = rl.quaternion_multiply(yaw, pitch)
        rot = rl.quaternion_multiply(rot, roll)
        self.target_rotation = rl.quaternion_multiply(rot, self.target_rotation)
        self.rotation = rl.quaternion_slerp(self.rotation, self.target_rotation, 0.3)

        rot_matrix = rl.quaternion_to_matrix(self.rotation)
        forward = rl.vector3_transform(Vector3(0, 0, -1), rot_matrix)
        up = rl.vector3_transform(Vector3(0, 1, 0), rot_matrix)
        right = rl.vector3_transform(Vector3(1, 0, 0), rot_matrix)

        # apply movement
        acc = vec3_zero()
        if rl.is_key_down(KeyboardKey.KEY_W):
            acc = rl.vector3_add(acc, rl.vector3_scale(forward, move_speed))
        if rl.is_key_down(KeyboardKey.KEY_S):
            acc = rl.vector3_add(acc, rl.vector3_scale(forward, -move_speed))
        if rl.is_key_down(KeyboardKey.KEY_D):
            acc = rl.vector3_add(acc, rl.vector3_scale(right, move_speed))
        if rl.is_key_down(KeyboardKey.KEY_A):
            acc = rl.vector3_add(acc, rl.vector3_scale(right, -move_speed))
        if rl.is_key_down(KeyboardKey.KEY_SPACE):
            acc = rl.vector3_add(acc, rl.vector3_scale(up, move_speed))
        if rl.is_key_down(KeyboardKey.KEY_LEFT_CONTROL):
            acc = rl.vector3_add(acc, rl.vector3_scale(up, -move_speed))

        # update values
        self.vel = rl.vector3_add(self.vel, acc) # don't multiply by dt (impulse instead of force)
        self.pos = rl.vector3_add(self.pos, rl.vector3_scale(self.vel, dt))

        self.camera.up = up
        self.camera.position = self.pos
        self.camera.target = rl.vector3_add(self.camera.position, forward)

    def apply_gravity(self, G: float, dt: float, bodies: Iterable[Planet]):
        acc = vec3_zero()
        for p in bodies:
            dir = rl.vector3_subtract(p.pos, self.pos)
            distance = rl.vector3_length(dir)
            if distance < 0.05:
                continue # avoid numerical explosion

            normalized = rl.vector3_scale(dir, 1.0 / distance) # normalize `dir`
            acceleration = G * p.mass / (distance*distance)
            acc = rl.vector3_add(acc, rl.vector3_scale(normalized, acceleration))
        self.vel = rl.vector3_add(self.vel, rl.vector3_scale(acc, dt))

