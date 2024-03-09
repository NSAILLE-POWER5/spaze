from dataclasses import dataclass
from typing import Self
from math import sqrt, cos, sin

import pyray as rl
from pyray import Camera3D, Color, KeyboardKey, Matrix, PixelFormat, Rectangle, Vector2, Vector3, Vector4
from raylib.defines import PI

BLACK = Color(0, 0, 0, 255)
RAYWHITE = Color(245, 245, 245, 255)
WHITE = Color(255, 255, 255, 255)
BLANK = Color(0, 0, 0, 0)
RED = Color(255, 0, 0, 255)

def vec3_zero():
    return Vector3(0, 0, 0)


@dataclass
class Planet:
    pos: Vector3
    orbit_radius: float
    orbit_angle: float
    mass: float
    radius: float
    transform: Matrix

    def orbit(self, G: float, sun: Self, dt: float):
        """Simulate perfectly circular orbit with keplerian mechanics"""
        angular_speed = sqrt(G * sun.mass / (self.orbit_radius*self.orbit_radius))
        self.orbit_angle += angular_speed*dt
        if self.orbit_angle > 2*PI:
            self.orbit_angle -= 2*PI
        self.pos = Vector3(cos(self.orbit_angle)*self.orbit_radius, 0, sin(self.orbit_angle)*self.orbit_radius)

    def compute_transform(self):
        radius = self.radius
        pos = self.pos
        self.transform = rl.matrix_scale(radius, radius, radius)
        self.transform = rl.matrix_multiply(self.transform, rl.matrix_rotate_xyz(Vector3(PI/2, 0.0, rl.get_time()/10.0)))
        self.transform = rl.matrix_multiply(self.transform, rl.matrix_translate(pos.x, pos.y, pos.z))

@dataclass
class Player:
    pos: Vector3
    vel: Vector3
    camera: Camera3D

    def update(self, dt: float):
        """Update camera view angle and speed with inputs, and integrate position over speed"""
        mouse_speed = 1.0
        move_speed = 0.5

        # change view angles
        up = self.camera.up
        forward = rl.vector3_normalize(rl.vector3_subtract(self.camera.target, self.camera.position))

        d = rl.get_mouse_delta()
        if d.x != 0.0: # handle yaw = rotate around y axis
            forward = rl.vector3_rotate_by_axis_angle(forward, up, mouse_speed * -d.x/180.0)

        right = rl.vector3_normalize(rl.vector3_cross_product(forward, up))
        if d.y != 0.0: # handle pitch = rotate around (local) x axis
            forward = rl.vector3_rotate_by_axis_angle(forward, right, mouse_speed * -d.y/180.0)

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
        self.camera.position = self.pos
        self.camera.target = rl.vector3_add(self.camera.position, forward)

    def apply_gravity(self, G: float, planets: list[Planet]):
        acc = vec3_zero()
        for i in range(len(planets)):
            p = planets[i]

            dir = rl.vector3_subtract(p.pos, self.pos)
            distance = rl.vector3_length(dir)
            if distance < 0.05:
                continue # avoid numerical explosion

            normalized = rl.vector3_scale(dir, 1.0 / distance) # normalize `dir`
            acceleration = G * p.mass / (distance*distance)
            acc = rl.vector3_add(acc, rl.vector3_scale(normalized, acceleration))


def main():
    rl.init_window(800, 800, "Spaze")
    rl.set_target_fps(60)
    rl.set_window_state(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE)

    sphere = rl.gen_mesh_sphere(1, 24, 24)

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
        Planet(vec3_zero(), 0, 0, 300, 15, rl.matrix_identity()),
        Planet(vec3_zero(), 20, 0, 10, 1.5, rl.matrix_identity()),
        Planet(vec3_zero(), 50, 0, 4, 1, rl.matrix_identity()),
        Planet(vec3_zero(), 120, 0, 30, 2, rl.matrix_identity()),
    ]

    player = Player(
        Vector3(0, 0, -50),
        Vector3(5, 0, 0),
        rl.Camera3D(
            Vector3(0, 0, -50),
            Vector3(0, 0, 0),
            Vector3(0, 1, 0),
            60,
            rl.CameraProjection.CAMERA_PERSPECTIVE
        )
    )

    rl.disable_cursor()

    post_process_shader = rl.load_shader("", "post_process.glsl")
    # sun_render = rl.load_render_texture(800, 800)

    dt = 1 / 60
    while not rl.window_should_close():
        player.apply_gravity(20, planets)
        player.update(dt)

        # apply_gravity(1, planets)
        for i in range(1, len(planets)):
            # planet.integrate(dt)
            planets[i].orbit(1, planets[0], dt)

        for planet in planets:
            planet.compute_transform()

        rl.set_shader_value(planet_shader, u_view_pos, player.camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)
        rl.set_shader_value(planet_shader, u_sun_pos, planets[0].pos, rl.ShaderAttributeDataType.SHADER_ATTRIB_VEC3)

        rl.set_shader_value(sun_shader, sun_u_view_pos, player.camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)
        rl.set_shader_value(sun_shader, sun_u_time, rl.get_time(), rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)

        rl.begin_drawing()
        rl.clear_background(BLACK)

        rl.begin_mode_3d(player.camera)

        # draw sun with bloom 
        rl.begin_shader_mode(post_process_shader)
        rl.draw_mesh(sphere, sun_mat, planets[0].transform)
        rl.end_shader_mode()

        # draw planets
        for i in range(1, len(planets)):
            rl.draw_mesh(sphere, planet_mat, planets[i].transform)

        rl.draw_circle_3d(vec3_zero(), 50, Vector3(1, 0, 0), 90, RED)

        rl.end_mode_3d()

        # draw UI
        rl.draw_fps(10, 10)

        cx = rl.get_render_width()/2
        cy = rl.get_render_height()/2
        rl.draw_line_v(Vector2(cx, cy - 6), Vector2(cx, cy + 6), WHITE)
        rl.draw_line_v(Vector2(cx - 6, cy), Vector2(cx + 6, cy), WHITE)

        # rl.draw_texture_ex(sun_render.texture, Vector2(0, 0), 0.0, 0.1, WHITE);
        # rl.draw_texture_ex(sun_render.depth, Vector2(80, 0), 0.0, 0.1, WHITE);

        rl.end_drawing()


if __name__ == '__main__':
    main()
