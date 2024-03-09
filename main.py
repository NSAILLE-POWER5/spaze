from dataclasses import dataclass

import pyray as rl
from pyray import Color, KeyboardKey, Matrix, Rectangle, Vector2, Vector3, Vector4
from raylib.defines import PI

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
        self.transform = rl.matrix_multiply(self.transform, rl.matrix_rotate_xyz(Vector3(PI/2, 0.0, rl.get_time()/10.0)))
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
    mouse_speed = 1.0
    move_speed = 0.5

    up = camera.up
    forward = rl.vector3_normalize(rl.vector3_subtract(camera.target, camera.position))

    d = rl.get_mouse_delta()
    if d.x != 0.0: # handle yaw = rotate around y axis
        forward = rl.vector3_rotate_by_axis_angle(forward, up, mouse_speed * -d.x/180.0)

    right = rl.vector3_normalize(rl.vector3_cross_product(forward, up))
    if d.y != 0.0: # handle pitch = rotate around (local) x axis
        forward = rl.vector3_rotate_by_axis_angle(forward, right, mouse_speed * -d.y/180.0)

    if rl.is_key_down(KeyboardKey.KEY_W):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(forward, move_speed))
    if rl.is_key_down(KeyboardKey.KEY_S):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(forward, -move_speed))
    if rl.is_key_down(KeyboardKey.KEY_D):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(right, move_speed))
    if rl.is_key_down(KeyboardKey.KEY_A):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(right, -move_speed))
    if rl.is_key_down(KeyboardKey.KEY_SPACE):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(up, move_speed))
    if rl.is_key_down(KeyboardKey.KEY_LEFT_CONTROL):
        camera.position = rl.vector3_add(camera.position, rl.vector3_scale(up, -move_speed))
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

    planet_shader = rl.load_shader("planet_vert.glsl", "planet_frag.glsl")
    u_ambient = rl.get_shader_location(planet_shader, "ambient")
    u_sun_pos = rl.get_shader_location(planet_shader, "sunPos")
    u_view_pos = rl.get_shader_location(planet_shader, "viewPos")

    rl.set_shader_value(planet_shader, u_ambient, Vector4(0.1, 0.1, 0.1, 1.0), rl.ShaderUniformDataType.SHADER_UNIFORM_VEC4)
    planet_shader.locs[rl.ShaderLocationIndex.SHADER_LOC_VECTOR_VIEW] = u_view_pos

    planet_mat = rl.load_material_default()
    planet_mat.shader = planet_shader

    sun_shader = rl.load_shader("sun_vert.glsl", "sun_frag.glsl")
    sun_u_view_pos = rl.get_shader_location(sun_shader, "viewPos")
    sun_u_time = rl.get_shader_location(sun_shader, "time")

    sun_texture = rl.load_texture("./sun.jpg")

    sun_mat = rl.load_material_default()
    sun_mat.maps[rl.MaterialMapIndex.MATERIAL_MAP_ALBEDO].texture = sun_texture
    sun_mat.shader = sun_shader

    planets = [
        Planet(vec3_zero(), vec3_zero(), vec3_zero(), 300, 15, rl.matrix_identity()),
        Planet(Vector3(50, 3, 0), Vector3(0, 0, 1), vec3_zero(), 4, 1, rl.matrix_identity()),
    ]

    rl.disable_cursor()

    post_process_shader = rl.load_shader("", "post_process.glsl")
    sun_render = rl.load_render_texture(800, 800)

    dt = 1 / 60
    while not rl.window_should_close():
        if rl.is_window_resized():
            sun_render = rl.load_render_texture(rl.get_render_width(), rl.get_render_height())

        update_camera(camera)

        apply_gravity(1, planets)
        for planet in planets:
            planet.integrate(dt)
            planet.compute_transform()

        rl.set_shader_value(planet_shader, u_view_pos, camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)
        rl.set_shader_value(planet_shader, u_sun_pos, planets[0].pos, rl.ShaderAttributeDataType.SHADER_ATTRIB_VEC3)

        rl.set_shader_value(sun_shader, sun_u_view_pos, camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)
        rl.set_shader_value(sun_shader, sun_u_time, rl.get_time(), rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)

        # render 3d scene
        rl.begin_texture_mode(sun_render)
        rl.clear_background(BLACK)

        rl.begin_mode_3d(camera)

        # draw sun
        rl.draw_mesh(sphere, sun_mat, planets[0].transform)

        rl.end_mode_3d()
        rl.end_texture_mode()

        rl.begin_drawing()

        # draw sun with bloom 
        rl.begin_shader_mode(post_process_shader)

        src = Rectangle(0, 0, rl.get_render_width(), -rl.get_render_height())
        dest = Rectangle(0, 0, rl.get_render_width(), rl.get_render_height())
        rl.draw_texture_pro(sun_render.texture, src, dest, Vector2(0, 0), 0.0, WHITE)
        rl.end_shader_mode()

        rl.begin_mode_3d(camera)

        # draw planets
        for i in range(1, len(planets)):
            rl.draw_mesh(sphere, planet_mat, planets[i].transform)

        rl.end_mode_3d()

        # draw UI
        rl.draw_fps(10, 10)
        rl.end_texture_mode()

        cx = rl.get_render_width()/2
        cy = rl.get_render_height()/2
        rl.draw_line_v(Vector2(cx, cy - 6), Vector2(cx, cy + 6), WHITE)
        rl.draw_line_v(Vector2(cx - 6, cy), Vector2(cx + 6, cy), WHITE)
        # rl.draw_text("hello, world!", 10, 40, 20, BLACK)

        rl.end_drawing()


if __name__ == '__main__':
    main()
