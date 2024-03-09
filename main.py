from dataclasses import dataclass
from typing import Self

import pyray as rl
from pyray import Color, KeyboardKey, Matrix, Vector2, Vector3, Vector4

BLACK = Color(0, 0, 0, 255)
RAYWHITE = Color(245, 245, 245, 255)
WHITE = Color(255, 255, 255, 255)

def vec3_zero():
    return Vector3(0, 0, 0)

@dataclass
class Planet:
    pos: Vector3
    speed: Vector3
    acc: Vector3
    mass: float
    radius: float
    transform: Matrix

    def integrate(self, dt: float):
        self.speed = rl.vector3_add(self.speed, rl.vector3_scale(self.acc, dt))
        self.pos = rl.vector3_add(self.pos, rl.vector3_scale(self.speed, dt))
        self.acc = Vector3(0, 0, 0)

    def compute_transform(self):
        radius = self.radius
        pos = self.pos
        self.transform = rl.matrix_scale(radius, radius, radius)
        self.transform = rl.matrix_multiply(self.transform, rl.matrix_translate(pos.x, pos.y, pos.z))

def apply_gravity(G: float, planets: list[Planet]):
    for i in range(len(planets)):
        # apply acceleration on both objects in the pair at once
        # don't iterate on previous objects (and on yourself), because they have already been computed
        for j in range(i+1, len(planets)):
            p1 = planets[i]
            p2 = planets[j]

            p1_to_p2 = rl.vector3_subtract(p2.pos, p1.pos)
            distance = rl.vector3_length(p1_to_p2)
            if distance < 0.05:
                continue # avoid numerical explosion

            normalized = rl.vector3_scale(p1_to_p2, 1.0 / distance) # normalize `p1_to_p2`
            force = G * p1.mass * p2.mass / (distance*distance)

            p1_acc = rl.vector3_scale(normalized, force / p1.mass)
            p2_acc = rl.vector3_scale(normalized, -force / p2.mass) # p2's acceleration is reversed

            p1.acc = rl.vector3_add(p1.acc, p1_acc)
            p2.acc = rl.vector3_add(p2.acc, p2_acc)


def update_camera(camera: rl.Camera3D):
    up = camera.up
    forward = rl.vector3_normalize(rl.vector3_subtract(camera.target, camera.position))

    d = rl.get_mouse_delta()
    if d.x != 0.0: # handle yaw = rotate around y axis
        forward = rl.vector3_rotate_by_axis_angle(forward, up, -d.x/180.0)

    right = rl.vector3_normalize(rl.vector3_cross_product(forward, up))
    if d.y != 0.0: # handle pitch = rotate around (local) x axis
        forward = rl.vector3_rotate_by_axis_angle(forward, right, -d.y/180.0)

    if rl.is_key_down(KeyboardKey.KEY_W):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(forward, 0.2))
    if rl.is_key_down(KeyboardKey.KEY_S):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(forward, -0.2))
    if rl.is_key_down(KeyboardKey.KEY_D):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(right, 0.2))
    if rl.is_key_down(KeyboardKey.KEY_A):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(right, -0.2))
    if rl.is_key_down(KeyboardKey.KEY_SPACE):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(up, 0.1))
    if rl.is_key_down(KeyboardKey.KEY_LEFT_CONTROL):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(up, -0.1))
    camera.target = rl.vector3_add(camera.position, forward)

def main():
    rl.init_window(800, 800, "Spaze")
    rl.set_target_fps(60)
    rl.set_window_state(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE)

    camera = rl.Camera3D(
        Vector3(0, 3, -30),
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
        Planet(vec3_zero(), vec3_zero(), vec3_zero(), 300, 15, rl.matrix_identity()),
        Planet(Vector3(50, 3, 0), Vector3(0, 0, 5), vec3_zero(), 4, 1, rl.matrix_identity()),
    ]

    rl.disable_cursor()

    dt = 1 / 60
    while not rl.window_should_close():
        update_camera(camera)

        apply_gravity(1, planets)
        for planet in planets:
            planet.integrate(dt)
            planet.compute_transform()

        rl.begin_drawing()
        rl.clear_background(BLACK)

        rl.begin_mode_3d(camera)

        for planet in planets:
            rl.draw_mesh(sphere, mat, planet.transform)

        rl.set_shader_value(shader, u_view_pos, camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)

        rl.end_mode_3d()

        rl.draw_fps(10, 10)

        cx = rl.get_render_width()/2
        cy = rl.get_render_height()/2
        rl.draw_line_v(Vector2(cx, cy - 6), Vector2(cx, cy + 6), WHITE)
        rl.draw_line_v(Vector2(cx - 6, cy), Vector2(cx + 6, cy), WHITE)
        # rl.draw_text("hello, world!", 10, 40, 20, BLACK)

        rl.end_drawing()

if __name__ == '__main__':
    main()
