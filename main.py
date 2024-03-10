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
    vel: Vector3 # instantaneous velocity
    orbit_radius: float
    orbit_angle: float
    orbit_center: Self | None
    mass: float
    radius: float
    transform: Matrix

    def __init__(self, orbit_radius: float, orbit_center: Self | None, mass: float, radius: float):
        self.pos = vec3_zero()
        self.vel = vec3_zero()
        self.orbit_radius = orbit_radius
        self.orbit_angle = 0
        self.orbit_center = orbit_center
        self.mass = mass
        self.radius = radius
        self.transform = rl.matrix_identity()

    def orbit(self, G: float, dt: float):
        """Simulate perfectly circular orbit with keplerian mechanics"""
        if self.orbit_center == None:
            return

        # For a perfectly circular orbit: (https://en.wikipedia.org/wiki/Circular_orbit)
        # acceleration = angular_speed^2 * radius
        # angular_speed = sqrt(acceleration / radius)

        # acceleration = G * m1 * m2 / radius^2 / m2
        #              = G * m1 / radius^2
        #
        # angular_speed = sqrt(G * m1 / radius^3)

        angular_speed = sqrt(G * self.orbit_center.mass / (self.orbit_radius**3))
        self.orbit_angle += angular_speed*dt
        if self.orbit_angle > 2*PI:
            self.orbit_angle -= 2*PI
        self.pos = Vector3(cos(self.orbit_angle)*self.orbit_radius, 0, sin(self.orbit_angle)*self.orbit_radius)
        self.pos = rl.vector3_add(self.pos, self.orbit_center.pos)

        # get instantaneous velocity:
        # velocity^2 / r = angular_speed^2 * r
        # velocity = sqrt(angular_speed^2 * r^2)
        # velocty = angular_speed * r
        velocity = angular_speed * self.orbit_radius
        self.vel = rl.vector3_scale(Vector3(-sin(self.orbit_angle), 0, cos(self.orbit_angle)), velocity)

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
        move_speed = 0.05

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

    def apply_gravity(self, G: float, dt: float, planets: list[Planet]):
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
        self.vel = rl.vector3_add(self.vel, rl.vector3_scale(acc, dt))


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

    planets = [ Planet(0, None, 5000, 10 ) ]

    planets.extend([
        Planet(180, planets[0], 50, 2.5),
        Planet(290, planets[0], 40, 2),
        Planet(500, planets[0], 600, 8),
    ])

    player = Player(
        Vector3(0, 0, -300),
        Vector3(5, 0, 0),
        rl.Camera3D(
            Vector3(0, 0, -150),
            Vector3(0, 0, 0),
            Vector3(0, 1, 0),
            60,
            rl.CameraProjection.CAMERA_PERSPECTIVE
        )
    )

    rl.disable_cursor()

    post_process_shader = rl.load_shader("", "post_process.glsl")
    # sun_render = rl.load_render_texture(800, 800)

    G = 50
    dt = 1 / 60
    while not rl.window_should_close():
        for planet in planets:
            planet.orbit(G, dt)
            planet.compute_transform()

        player.apply_gravity(G, dt, planets)
        player.update(dt)

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
            planet = planets[i]
            rl.draw_mesh(sphere, planet_mat, planet.transform)
            rl.draw_line_3d(planet.pos, rl.vector3_add(planet.pos, rl.vector3_scale(planet.vel, 60)), RED)

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
