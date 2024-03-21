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

    def handle_mouse_input(self, dt: float):
        """Update view angle"""
        mouse_speed = 0.3
        roll_speed = 0.5

        # calculate local coordinate system
        rot_matrix = rl.quaternion_to_matrix(self.rotation)
        forward = rl.vector3_transform(Vector3(0, 0, -1), rot_matrix)
        up = rl.vector3_transform(Vector3(0, 1, 0), rot_matrix)
        right = rl.vector3_transform(Vector3(1, 0, 0), rot_matrix)

        # get rotation delta
        d = rl.get_mouse_delta()
        yaw = rl.quaternion_from_axis_angle(up, -d.x*mouse_speed*dt)
        pitch = rl.quaternion_from_axis_angle(right, -d.y*mouse_speed*dt)
        roll = rl.quaternion_from_axis_angle(forward, roll_speed*(float(rl.is_key_down(KeyboardKey.KEY_E))-float(rl.is_key_down(KeyboardKey.KEY_Q)))*dt)

        # apply it
        rot = rl.quaternion_multiply(yaw, pitch)
        rot = rl.quaternion_multiply(rot, roll)
        self.target_rotation = rl.quaternion_multiply(rot, self.target_rotation)
        self.rotation = rl.quaternion_slerp(self.rotation, self.target_rotation, 0.3)

    def handle_keyboard_input(self):
        """Accelerate ship with keyboard inputs, and sync raylib camera with player movement"""
        move_speed = 0.2

        # calculate local coordinate system
        rot_matrix = rl.quaternion_to_matrix(self.rotation)
        forward = rl.vector3_transform(Vector3(0, 0, -1), rot_matrix)
        up = rl.vector3_transform(Vector3(0, 1, 0), rot_matrix)
        right = rl.vector3_transform(Vector3(1, 0, 0), rot_matrix)

        # apply movement
        forward_input = float(rl.is_key_down(KeyboardKey.KEY_W))-float(rl.is_key_down(KeyboardKey.KEY_S))
        right_input = float(rl.is_key_down(KeyboardKey.KEY_D))-float(rl.is_key_down(KeyboardKey.KEY_A))
        up_input = float(rl.is_key_down(KeyboardKey.KEY_SPACE))-float(rl.is_key_down(KeyboardKey.KEY_LEFT_CONTROL))

        acc = vec3_zero()
        acc = rl.vector3_add(acc, rl.vector3_scale(forward, forward_input))
        acc = rl.vector3_add(acc, rl.vector3_scale(right, right_input))
        acc = rl.vector3_add(acc, rl.vector3_scale(up, up_input))
        acc = rl.vector3_scale(acc, move_speed)

        self.vel = rl.vector3_add(self.vel, acc) # don't multiply by dt (impulse instead of force)

    def apply_gravity(self, G: float, dt: float, bodies: Iterable[Planet]):
        """Apply gravity force to the player from all bodies"""
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

    def integrate(self, dt: float):
        """Apply velocity to position"""
        self.pos = rl.vector3_add(self.pos, rl.vector3_scale(self.vel, dt))
    
    def sync_camera(self):
        """Synchronise the camera with the player's transforms"""
        rot_matrix = rl.quaternion_to_matrix(self.rotation)
        forward = rl.vector3_transform(Vector3(0, 0, -1), rot_matrix)
        up = rl.vector3_transform(Vector3(0, 1, 0), rot_matrix)

        # sync camera
        self.camera.up = up
        self.camera.position = self.pos
        self.camera.target = rl.vector3_add(self.camera.position, forward)
