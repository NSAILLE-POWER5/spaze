from dataclasses import dataclass
from typing import Self
from math import inf, sqrt, cos, sin, tan, log1p

import pyray as rl
from pyray import Camera3D, Color, KeyboardKey, Matrix, Rectangle, Vector2, Vector3, Vector4
from raylib.defines import DEG2RAD, PI

BLACK = Color(0, 0, 0, 255)
RAYWHITE = Color(245, 245, 245, 255)
WHITE = Color(255, 255, 255, 255)
BLANK = Color(0, 0, 0, 0)
RED = Color(255, 0, 0, 255)

def vec3_zero() -> Vector3:
    return Vector3(0, 0, 0)

def print_vec3(v: Vector3):
    print(v.x, v.y, v.z)

def cot(x: float) -> float:
    """Returns the cotangent of `x`"""
    return 1 / tan(x)

def get_projected_sphere_radius(cam: Camera3D, screen_height: float, center: Vector3, radius: float) -> float:
    """Get the screen space radius a sphere will be drawn as in pixels"""
    # https://stackoverflow.com/a/21649403

    d = rl.vector_3distance(cam.position, center)
    # convert camera fov to radians
    fov = cam.fovy*DEG2RAD / 2
    pr = cot(fov) * radius / sqrt(d*d - radius*radius)
    return pr * screen_height / 2

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
        move_speed = 0.2

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
        closest, closest_dist = -1, inf

        acc = vec3_zero()
        for i in range(len(planets)):
            p = planets[i]

            dir = rl.vector3_subtract(p.pos, self.pos)
            distance = rl.vector3_length(dir)
            if distance < 0.05:
                continue # avoid numerical explosion
            if distance < closest_dist:
                closest = i
                closest_dist = distance

            normalized = rl.vector3_scale(dir, 1.0 / distance) # normalize `dir`
            acceleration = G * p.mass / (distance*distance)
            acc = rl.vector3_add(acc, rl.vector3_scale(normalized, acceleration))
        self.vel = rl.vector3_add(self.vel, rl.vector3_scale(acc, dt))
        self.camera.target = rl.vector3_add(self.camera.target, rl.vector3_scale(acc, dt))


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

    planets = [ Planet(0, None, 5000, 20 ) ]

    planets.extend([
        Planet(180, planets[0], 50, 5),
        Planet(290, planets[0], 40, 4),
        Planet(500, planets[0], 600, 16),
    ])

    planets.extend([
        Planet(40, planets[3], 5, 1)
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

    bloom_shader = rl.load_shader("", "bloom.glsl")

    bloom_target = rl.load_render_texture(800, 800)
    target = rl.load_render_texture(800, 800)
    rl.set_texture_wrap(target.texture, rl.TextureWrap.TEXTURE_WRAP_CLAMP)

    selected_planet = -1

    G = 5
    dt = 1 / 60
    while not rl.window_should_close():
        inverted_render_rect = Rectangle(0, 0, rl.get_render_width(), -rl.get_render_height())
        if rl.is_window_resized():
            rl.unload_render_texture(bloom_target)
            rl.unload_render_texture(target)

            bloom_target = rl.load_render_texture(rl.get_render_width(), rl.get_render_height())
            target = rl.load_render_texture(rl.get_render_width(), rl.get_render_height())
            rl.set_texture_wrap(target.texture, rl.TextureWrap.TEXTURE_WRAP_CLAMP)

        cx = rl.get_render_width()/2
        cy = rl.get_render_height()/2

        for planet in planets:
            planet.orbit(G, dt)
            planet.compute_transform()

        player.apply_gravity(G, dt, planets)
        player.update(dt)

        if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
            ray = rl.get_mouse_ray(Vector2(cx, cy), player.camera)
            for i, planet in enumerate(planets):
                coll = rl.get_ray_collision_sphere(ray, planet.pos, planet.radius)
                if coll.hit:
                    if selected_planet == i:
                        selected_planet = -1
                    else:
                        selected_planet = i
        if rl.is_key_down(rl.KeyboardKey.KEY_G):
            player.camera.target = Vector3(0, 0, 0)

        rl.set_shader_value(planet_shader, u_view_pos, player.camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)
        rl.set_shader_value(planet_shader, u_sun_pos, planets[0].pos, rl.ShaderAttributeDataType.SHADER_ATTRIB_VEC3)

        rl.set_shader_value(sun_shader, sun_u_view_pos, player.camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)
        rl.set_shader_value(sun_shader, sun_u_time, rl.get_time(), rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)

        # render sun first to the target texture
        rl.begin_texture_mode(target)
        rl.clear_background(BLACK)

        rl.begin_mode_3d(player.camera)
        rl.draw_mesh(sphere, sun_mat, planets[0].transform)
        rl.end_mode_3d()

        rl.end_texture_mode()

        # apply bloom effect to sun on other texture
        rl.begin_texture_mode(bloom_target)

        rl.begin_shader_mode(bloom_shader)
        rl.draw_texture_rec(target.texture, inverted_render_rect, Vector2(0, 0), WHITE);
        rl.end_shader_mode()

        rl.end_texture_mode()

        # start normal rendering
        rl.begin_texture_mode(target)

        # copy the info back
        rl.draw_texture_rec(bloom_target.texture, inverted_render_rect, Vector2(0, 0), WHITE);

        # draw planets
        rl.begin_mode_3d(player.camera)
        for i in range(1, len(planets)):
            planet = planets[i]
            rl.draw_mesh(sphere, planet_mat, planet.transform)
        rl.end_mode_3d()

        # draw UI
        rl.draw_fps(10, 10)

        if selected_planet != -1:
            # show the relative velocity between the player and the selected planet
            planet = planets[selected_planet]
            p1 = rl.get_world_to_screen(planet.pos, player.camera)
            vel = rl.vector3_subtract(player.vel, planet.vel)
            # divide by sqrt(length) 
            # make speed scale logarithmically
            vel_length = rl.vector3_length(vel)
            vel = rl.vector3_scale(vel, 5*log1p(vel_length) / vel_length)

            p2 = rl.get_world_to_screen(rl.vector3_add(planet.pos, vel), player.camera)
            rl.draw_line_v(Vector2(p1.x, p1.y), Vector2(p2.x, p2.y), WHITE)

            projected_radius = get_projected_sphere_radius(player.camera, rl.get_render_height(), planet.pos, planet.radius)
            rl.draw_circle_lines_v(p1, projected_radius + 10, WHITE)

        rl.draw_line_v(Vector2(cx, cy - 6), Vector2(cx, cy + 6), WHITE)
        rl.draw_line_v(Vector2(cx - 6, cy), Vector2(cx + 6, cy), WHITE)

        rl.end_texture_mode()

        # draw target to screen
        rl.begin_drawing()
        rl.draw_texture_rec(target.texture, inverted_render_rect, Vector2(0, 0), WHITE);
        rl.end_drawing()


if __name__ == '__main__':
    main()
