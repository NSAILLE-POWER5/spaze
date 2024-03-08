from dataclasses import dataclass
from math import cos, sin

import pyray as rl
from pyray import Color, KeyboardKey, Matrix, Vector3, Vector4, clamp
from raylib.defines import PI

BLACK = Color(0, 0, 0, 255)
RAYWHITE = Color(245, 245, 245, 255)

@dataclass
class Planet:
    pos: Vector3
    mass: float
    radius: float
    transform: Matrix

    def compute_transform(self):
        radius = self.radius
        pos = self.pos
        self.transform = rl.matrix_scale(radius, radius, radius)
        self.transform = rl.matrix_multiply(self.transform, rl.matrix_translate(pos.x, pos.y, pos.z))

rl.init_window(800, 800, "Spaze")
rl.set_target_fps(60)

camera = rl.Camera3D(
    Vector3(0, 3, -8),
    Vector3(0, 0, 0),
    Vector3(0, 1, 0),
    60,
    rl.CameraProjection.CAMERA_PERSPECTIVE
)

sphere = rl.gen_mesh_sphere(1, 16, 16)

shader = rl.load_shader("default_vert.glsl", "default_frag.glsl")
u_ambient = rl.get_shader_location(shader, "ambient")
u_sun_dir = rl.get_shader_location(shader, "sunDir")
u_view_pos = rl.get_shader_location(shader, "viewPos")

rl.set_shader_value(shader, u_ambient, Vector4(0.1, 0.1, 0.1, 1.0), rl.ShaderUniformDataType.SHADER_UNIFORM_VEC4)
rl.set_shader_value(shader, u_sun_dir, rl.vector3_normalize(Vector3(0.5, 1.0, 0.2)), rl.ShaderAttributeDataType.SHADER_ATTRIB_VEC3)

shader.locs[rl.ShaderLocationIndex.SHADER_LOC_VECTOR_VIEW] = u_view_pos

mat = rl.load_material_default()
mat.shader = shader

planets = [
    Planet(Vector3(0, 0, 0), 100, 1, rl.matrix_identity())
]

rl.disable_cursor()

while not rl.window_should_close():
    rl.begin_drawing()
    rl.clear_background(BLACK)

    rl.begin_mode_3d(camera)

    # rl.draw_mesh(sphere, mat, rl.matrix_identity())
    
    # for planet in planets:
    #     planet.compute_transform()
    #
    for planet in planets:
        rl.draw_mesh(sphere, mat, planet.transform)

    up = camera.up
    forward = rl.vector3_normalize(rl.vector3_subtract(camera.target, camera.position))

    d = rl.get_mouse_delta()
    if d.x != 0.0: # handle yaw = rotate around y axis
        forward = rl.vector3_rotate_by_axis_angle(forward, up, -d.x/180.0)

    right = rl.vector3_normalize(rl.vector3_cross_product(forward, up))
    if d.y != 0.0: # handle pitch = rotate around (local) x axis
        forward = rl.vector3_rotate_by_axis_angle(forward, right, -d.y/180.0)

    if rl.is_key_down(KeyboardKey.KEY_W):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(forward, 0.1))
    if rl.is_key_down(KeyboardKey.KEY_S):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(forward, -0.1))
    if rl.is_key_down(KeyboardKey.KEY_D):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(right, 0.1))
    if rl.is_key_down(KeyboardKey.KEY_A):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(right, -0.1))
    if rl.is_key_down(KeyboardKey.KEY_SPACE):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(up, 0.1))
    if rl.is_key_down(KeyboardKey.KEY_LEFT_CONTROL):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(up, -0.1))

    camera.target = rl.vector3_add(camera.position, forward)

    # rl.draw_line_3d(pos, rl.vector3_add(pos, view_vector), Color(255, 0, 0, 255))
    # rl.draw_sphere(pos, 0.1, Color(255, 255, 0, 255))

    # rl.update_camera(camera, rl.CameraMode.CAMERA_CUSTOM)

    rl.set_shader_value(shader, u_view_pos, camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)

    rl.end_mode_3d()

    rl.draw_fps(10, 10)
    # rl.draw_text("hello, world!", 10, 40, 20, BLACK)

    rl.end_drawing()
