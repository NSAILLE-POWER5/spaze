from math import tan, radians, sqrt
from typing import TypeAlias
from pyray import Vector3, Camera3D, Vector4, vector_3distance

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
