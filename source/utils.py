from math import tan, radians, sqrt
from typing import TypeAlias

from pyray import Vector3, Camera3D, Vector4, vector_3distance, get_random_value, remap
import pyray as rl
from raylib.defines import RL_TRIANGLES

Quat: TypeAlias = Vector4

def vec3_zero() -> Vector3:
    return Vector3(0, 0, 0)

def print_vec3(v: Vector3):
    print(v.x, v.y, v.z)

def cot(x: float) -> float:
    """Returns the cotangent of `x`"""
    return 1 / tan(x)

def get_projected_sphere_radius(cam: Camera3D, screen_height: float, center: Vector3, radius: float) -> float:
    """
    Get the screen space radius a sphere will be drawn as in pixels.
    Returns 0 if the camera is inside the sphere.
    """
    # https://stackoverflow.com/a/21649403

    d = vector_3distance(cam.position, center)
    if d < radius:
        return 0
    # convert camera fov to radians
    fov = radians(cam.fovy) / 2
    pr = cot(fov) * radius / sqrt(d*d - radius*radius)
    return pr * screen_height / 2

def randf() -> float:
    """Returns value between 0 (inclusive) and 1 (exclusive)"""
    return get_random_value(0, 32767)/32767

def randfr(min: float, max: float) -> float:
    """Returns a random floating point value between the mininum (inclusive) and the maximum (exclusive)"""
    return remap(randf(), 0.0, 1.0, min, max)

def draw_rectangle_tex_coords(x: float, y: float, w: float, h: float):
    """Draw a rectangle at the given coordinates with uvs (useful for 2d shaders)"""
    rl.rl_begin(RL_TRIANGLES)

    rl.rl_color4f(1.0, 1.0, 1.0, 1.0);

    rl.rl_tex_coord2f(0.0, 0.0)
    rl.rl_vertex2f(x, y)
    rl.rl_tex_coord2f(0.0, 1.0)
    rl.rl_vertex2f(x, y + h)
    rl.rl_tex_coord2f(1.0, 0.0)
    rl.rl_vertex2f(x + w, y)

    rl.rl_tex_coord2f(1.0, 0.0)
    rl.rl_vertex2f(x + w, y)
    rl.rl_tex_coord2f(0.0, 1.0)
    rl.rl_vertex2f(x, y + h)
    rl.rl_tex_coord2f(1.0, 1.0)
    rl.rl_vertex2f(x + w, y + h)

    rl.rl_end()
