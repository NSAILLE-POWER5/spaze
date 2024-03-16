from dataclasses import dataclass
from typing import Self, TypeAlias
from math import sqrt, cos, sin, tan, pi, radians, copysign, log1p

import pyray as rl
from pyray import Camera3D, Color, KeyboardKey, MaterialMapIndex, Matrix, Rectangle, Vector2, Vector3, Vector4
from raylib import ffi

from icosphere import gen_icosphere

BLACK = Color(0, 0, 0, 255)
RAYWHITE = Color(245, 245, 245, 255)
WHITE = Color(255, 255, 255, 255)
BLANK = Color(0, 0, 0, 0)
RED = Color(255, 0, 0, 255)

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

    d = rl.vector_3distance(cam.position, center)
    if d < radius:
        return 0
    # convert camera fov to radians
    fov = radians(cam.fovy) / 2
    pr = cot(fov) * radius / sqrt(d*d - radius*radius)
    return pr * screen_height / 2

@dataclass
class Planet:
    pos: Vector3
    vel: Vector3 # instantaneous velocity
    orbit_radius: float
    orbit_angle: float
    orbit_center: Self | None
    color : Color
    type : int 
    mass: float
    radius: float
    transform: Matrix

    def __init__(self, orbit_radius: float, orbit_center: Self | None, G: float, surface_gravity: float, radius: float):
        self.pos = vec3_zero()
        self.vel = vec3_zero()
        self.color = Color(rl.get_random_value(50, 200), rl.get_random_value(50, 200), rl.get_random_value(50, 200),255)
        self.type = rl.get_random_value(0, 3)
        self.orbit_radius = orbit_radius
        self.orbit_angle = 0
        self.orbit_center = orbit_center
        self.mass = radius*radius*surface_gravity / G # set mass based on surface gravity
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
        if self.orbit_angle > 2*pi:
            self.orbit_angle -= 2*pi
        self.pos = Vector3(cos(self.orbit_angle)*self.orbit_radius, 0, sin(self.orbit_angle)*self.orbit_radius)
        self.pos = rl.vector3_add(self.pos, self.orbit_center.pos)

        # get instantaneous velocity:
        # velocity^2 / r = angular_speed^2 * r
        # velocity = sqrt(angular_speed^2 * r^2)
        # velocty = angular_speed * r
        velocity = angular_speed * self.orbit_radius

        self.vel = rl.vector3_scale(Vector3(-sin(self.orbit_angle), 0, cos(self.orbit_angle)), velocity)
        # add their parent's velocity
        self.vel = rl.vector3_add(self.vel, self.orbit_center.vel)

    def compute_transform(self):
        radius = self.radius
        pos = self.pos
        self.transform = rl.matrix_scale(radius, radius, radius)
        self.transform = rl.matrix_multiply(self.transform, rl.matrix_rotate_xyz(Vector3(pi/2, 0.0, rl.get_time()/10.0)))
        self.transform = rl.matrix_multiply(self.transform, rl.matrix_translate(pos.x, pos.y, pos.z))

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

    def apply_gravity(self, G: float, dt: float, planets: list[Planet]):
        # closest, closest_dist = -1, inf

        acc = vec3_zero()
        for i in range(len(planets)):
            p = planets[i]

            dir = rl.vector3_subtract(p.pos, self.pos)
            distance = rl.vector3_length(dir)
            if distance < 0.05:
                continue # avoid numerical explosion
            # if distance < closest_dist:
            #     closest = i
            #     closest_dist = distance

            normalized = rl.vector3_scale(dir, 1.0 / distance) # normalize `dir`
            acceleration = G * p.mass / (distance*distance)
            acc = rl.vector3_add(acc, rl.vector3_scale(normalized, acceleration))
        self.vel = rl.vector3_add(self.vel, rl.vector3_scale(acc, dt))


def main():
    rl.init_window(1280, 720, "Spaze")
    rl.set_target_fps(60)
    rl.set_window_state(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE)
    rl.set_exit_key(rl.KeyboardKey.KEY_NULL)

    G = 5
    dt = 1 / 60

    sphere = gen_icosphere(4).create_mesh()

    tera_texture = rl.load_texture("tera.png")
    jupiter_texture = rl.load_texture("jupiter.png")
    mercure_texture = rl.load_texture("mercury.png")
    neptune_texture = rl.load_texture("neptune.png")
    texture_types = [tera_texture, jupiter_texture, mercure_texture, neptune_texture]


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

    sun_texture = rl.load_texture("./sun.png")
    vaisseau = rl.load_texture("cockpit.png")

    sun_mat = rl.load_material_default()
    sun_mat.maps[rl.MaterialMapIndex.MATERIAL_MAP_ALBEDO].texture = sun_texture
    sun_mat.shader = sun_shader

    planets = [ Planet(0, None, G, 30, 200 ) ]

    planets.extend([
        Planet(500, planets[0], G, 6, 50),
        Planet(800, planets[0], G, 4, 30),
        Planet(1800, planets[0], G, 12, 100),
        Planet(700, planets[0], G, 6, 50),
        Planet(900, planets[0], G, 4, 30),
        Planet(1100, planets[0], G, 12, 100),
    ])

    planets.extend([
        Planet(190, planets[3], G, 2, 15)
    ])

    player = Player(
        Vector3(0, 0, -900),
        Vector3(5, 0, 0),
        rl.Camera3D(
            Vector3(0, 0, -150),
            Vector3(0, 0, 0),
            Vector3(0, 1, 0),
            60,
            rl.CameraProjection.CAMERA_PERSPECTIVE
        ),
        rl.quaternion_from_euler(0, pi, 0),
        rl.quaternion_from_euler(0, pi, 0)
    )

    ico = gen_icosphere(3).create_mesh()

    # initialize positions and transforms since the game is paused by default
    # and randomize orbit angles
    for planet in planets:
        planet.orbit_angle = rl.get_random_value(0, 1000)/1000 * 2 * pi
        planet.orbit(G, dt)
        planet.compute_transform()
    player.update(dt)

    bloom_shader = rl.load_shader("", "bloom.glsl")

    bloom_target = rl.load_render_texture(1280, 720)
    target = rl.load_render_texture(1280, 720)
    rl.set_texture_wrap(target.texture, rl.TextureWrap.TEXTURE_WRAP_CLAMP)

    selected_planet = -1

    paused = True

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

        if not paused:
            for planet in planets:
                planet.orbit(G, dt)
                planet.compute_transform()

            player.apply_gravity(G, dt, planets)
            player.update(dt)

            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                ray = rl.get_mouse_ray(Vector2(cx, cy), player.camera)
                for i, planet in enumerate(planets):
                    # skip if we're looking away from the planet
                    if rl.vector_3dot_product(ray.direction, rl.vector3_subtract(planet.pos, player.pos)) < 0:
                        continue

                    coll = rl.get_ray_collision_sphere(ray, planet.pos, planet.radius)
                    if coll.hit:
                        if selected_planet == i:
                            selected_planet = -1
                        else:
                            selected_planet = i
            if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
                rl.enable_cursor()
                paused = True
        else:
            for planet in planets:
                planet.compute_transform()

            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                rl.disable_cursor()
                paused = False


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

        # apply bloom effect to the sun
        rl.begin_texture_mode(bloom_target)

        rl.begin_shader_mode(bloom_shader)
        rl.draw_texture_rec(target.texture, inverted_render_rect, Vector2(0, 0), WHITE)
        rl.end_shader_mode()

        rl.end_texture_mode()

        # start normal rendering
        rl.begin_texture_mode(target)

        # copy texture back
        rl.draw_texture_rec(bloom_target.texture, inverted_render_rect, Vector2(0, 0), WHITE)

        # draw planets
        rl.begin_mode_3d(player.camera)
        for i in range(1, len(planets)):
            planet = planets[i]
            planet_mat.maps.color = planet.color
            planet_mat.maps[MaterialMapIndex.MATERIAL_MAP_ALBEDO].texture = texture_types[planet.type]
            rl.draw_mesh(sphere, planet_mat, planet.transform)
        rl.end_mode_3d()

        # draw UI
        rl.draw_fps(10, 10)

        if selected_planet != -1:
            # show the relative velocity between the player and the selected planet
            planet = planets[selected_planet]
            pos_diff = rl.vector3_subtract(planet.pos, player.pos)
            projected_radius = get_projected_sphere_radius(player.camera, rl.get_render_height(), planet.pos, planet.radius)
            # don't render if the planet is behind us
            if projected_radius > 0 and rl.vector_3dot_product(rl.vector3_subtract(player.camera.target, player.pos), pos_diff) > 0:
                # don't let the radius get bigger than half the screen
                projected_radius = min(min(projected_radius, cx), cy)

                vel = rl.vector3_subtract(player.vel, planet.vel)

                # scale vector logarithmically
                vel_length = rl.vector3_length(vel)
                scaled_vel = rl.vector3_scale(vel, 2*log1p(vel_length) / vel_length)

                # place first point in the direction of the planet (make it appear at its center)
                # but always have it at a fixed distance to remove perspective effect
                p1_world = rl.vector3_add(player.pos, rl.vector3_scale(rl.vector3_normalize(pos_diff), 30.0))
                p1 = rl.get_world_to_screen(p1_world, player.camera)
                p2 = rl.get_world_to_screen(rl.vector3_add(p1_world, scaled_vel), player.camera)

                # Draw thicker line under first (outline)

                rl.draw_circle_v(p1, 3, BLACK)
                rl.draw_line_ex(p1, Vector2(p2.x, p1.y), 3, BLACK)
                rl.draw_line_ex(p1, Vector2(p1.x, p2.y), 3, BLACK)
                rl.draw_line_v(p1, Vector2(p2.x, p1.y), WHITE)
                rl.draw_line_v(p1, Vector2(p1.x, p2.y), WHITE)

                radius = projected_radius + 20
                rl.draw_ring_lines(p1, radius, radius, 22.5, 22.5+45, 24, WHITE)
                rl.draw_ring_lines(p1, radius, radius, 112.5, 112.5+45, 24, WHITE)
                rl.draw_ring_lines(p1, radius, radius, 202.5, 202.5+45, 24, WHITE)
                rl.draw_ring_lines(p1, radius, radius, 292.5, 292.5+45, 24, WHITE)

                distance = rl.vector3_length(pos_diff)
                # if velocity points in the same direction as player->planet, then velocity is positive otherwise (points away), it's negative
                # dot product and divide by distance gives forward speed
                forward_speed = rl.vector_3dot_product(vel, pos_diff) / distance

                text_pos = Vector2(radius, -radius)
                if p1.y-radius < 0:
                    text_pos.y = radius
                text_pos = rl.vector2_scale(text_pos, 1 / sqrt(2)) # scale vector to circle of radius `radius`
                text_pos = rl.vector2_add(text_pos, p1)

                rl.draw_text("{:.1f} m".format(distance), int(text_pos.x), int(text_pos.y), 20, WHITE)
                rl.draw_text("{:.1f} m/s".format(forward_speed), int(text_pos.x), int(text_pos.y+20), 20, WHITE)

        rl.draw_line_v(Vector2(cx, cy - 6), Vector2(cx, cy + 6), WHITE)
        rl.draw_line_v(Vector2(cx - 6, cy), Vector2(cx + 6, cy), WHITE)

        rl.end_texture_mode()

        # draw target to screen
        rl.begin_drawing()
        rl.draw_texture_rec(target.texture, inverted_render_rect, Vector2(0, 0), WHITE)

        rl.draw_texture_pro(vaisseau, Rectangle(0, 0, 1280, 720),
                            Rectangle(0, 0, rl.get_render_width(), rl.get_render_height()), Vector2(0, 0), 0.0,
                            WHITE)


        if paused:
            # rl.draw_rectangle(0, 0, rl.get_render_width(), rl.get_render_height(), Color(0, 0, 0, 28))
            rl.draw_rectangle_rounded(Rectangle(cx - 50, cy - 15, 100, 30), 0.5, 16, BLACK)
            rl.draw_rectangle_rounded_lines(Rectangle(cx - 50, cy - 15, 100, 30), 0.5, 16, 3, WHITE)
            pause_width = rl.measure_text("Paused", 20)
            rl.draw_text("Paused", int(cx - pause_width/2), int(cy-10), 20, WHITE)

        rl.end_drawing()


if __name__ == '__main__':
    main()
