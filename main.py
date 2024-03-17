from math import pi, log1p

import pyray as rl
from pyray import Color, MaterialMapIndex, Rectangle, ShaderLocationIndex, Vector2, Vector3, Vector4
from raylib import ffi

from icosphere import gen_icosphere
from utils import get_projected_sphere_radius, randf
from player import Player
from system import Planet, System

BLACK = Color(0, 0, 0, 255)
RAYWHITE = Color(245, 245, 245, 255)
WHITE = Color(255, 255, 255, 255)
BLANK = Color(0, 0, 0, 0)
RED = Color(255, 0, 0, 255)

def main():
    rl.init_window(1280, 720, "Spaze")
    rl.set_target_fps(60)
    rl.set_window_state(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE)
    rl.set_exit_key(rl.KeyboardKey.KEY_NULL)

    G = 5
    dt = 1 / 60

    sphere = gen_icosphere(4).create_mesh()

    tera_texture = rl.load_texture("assets/tera.png")
    jupiter_texture = rl.load_texture("assets/jupiter.png")
    mercure_texture = rl.load_texture("assets/mercury.png")
    neptune_texture = rl.load_texture("assets/neptune.png")
    texture_types = [tera_texture, jupiter_texture, mercure_texture, neptune_texture]


    planet_shader = rl.load_shader("shaders/planet_vert.glsl", "shaders/planet_frag.glsl")
    u_ambient = rl.get_shader_location(planet_shader, "ambient")
    u_sun_pos = rl.get_shader_location(planet_shader, "sunPos")
    u_view_pos = rl.get_shader_location(planet_shader, "viewPos")

    rl.set_shader_value(planet_shader, u_ambient, Vector4(0.1, 0.1, 0.1, 1.0), rl.ShaderUniformDataType.SHADER_UNIFORM_VEC4)
    planet_shader.locs[rl.ShaderLocationIndex.SHADER_LOC_VECTOR_VIEW] = u_view_pos

    planet_mat = rl.load_material_default()
    planet_mat.shader = planet_shader

    sun_shader = rl.load_shader("shaders/sun_vert.glsl", "shaders/sun_frag.glsl")
    sun_u_view_pos = rl.get_shader_location(sun_shader, "viewPos")
    sun_u_time = rl.get_shader_location(sun_shader, "time")

    sun_texture = rl.load_texture("assets/sun.png")
    vaisseau = rl.load_texture("assets/cockpit.png")

    sun_mat = rl.load_material_default()
    sun_mat.maps[MaterialMapIndex.MATERIAL_MAP_ALBEDO].texture = sun_texture
    sun_mat.maps[MaterialMapIndex.MATERIAL_MAP_ALBEDO].color = Color(255, 210, 0, 255)
    sun_mat.shader = sun_shader

    system = System(Planet(0, None, G, 30, 200 ))

    system.add(Planet(500, system.bodies[0], G, 6, 50))
    system.add(Planet(800, system.bodies[0], G, 4, 30))
    system.add(Planet(1800, system.bodies[0], G, 12, 100))
    system.add(Planet(700, system.bodies[0], G, 6, 50))
    system.add(Planet(900, system.bodies[0], G, 4, 30))
    system.add(Planet(1100, system.bodies[0], G, 12, 100))

    system.add(Planet(190, system.bodies[3], G, 2, 15))

    # initialize positions and transforms since the game is paused by default
    # and randomize orbit angles
    for planet in system.planets():
        planet.orbit_angle = randf() * 2 * pi
    system.update(G, dt)

    player = Player(
        Vector3(0, 0, -1300),
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

    sky_model = rl.gen_mesh_sphere(1, 4, 4)

    # allocate an array of 1000 matrices
    sky_transforms = ffi.cast("Matrix *", rl.mem_alloc(1000*ffi.sizeof("Matrix")))
    for i in range(1000):
        # bundle points closer to the horizon line
        y = (randf()*2-1)*(randf()*2-1)*(randf()*2-1)

        v = Vector3(randf()*2 - 1, y, randf()*2 - 1)
        v = rl.vector3_scale(rl.vector3_normalize(v), 500)
        scale = randf() + 0.5
        sky_transforms[i] = rl.matrix_multiply(rl.matrix_scale(scale, scale, scale), rl.matrix_translate(v.x, v.y, v.z))

    sky_shader = rl.load_shader("shaders/sky_vert.glsl", "shaders/sky_frag.glsl")
    sky_shader.locs[ShaderLocationIndex.SHADER_LOC_MATRIX_MODEL] = rl.get_shader_location_attrib(sky_shader, "matModel")

    sky_mat = rl.load_material_default()
    sky_mat.shader = sky_shader

    player.update(dt)

    bloom_shader = rl.load_shader("", "shaders/bloom.glsl")

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
            system.update(G, dt)
            player.apply_gravity(G, dt, system.bodies)
            player.update(dt)

            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                ray = rl.get_mouse_ray(Vector2(cx, cy), player.camera)
                for i, planet in enumerate(system.bodies):
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
            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                rl.disable_cursor()
                paused = False


        rl.set_shader_value(planet_shader, u_view_pos, player.camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)
        rl.set_shader_value(planet_shader, u_sun_pos, system.bodies[0].pos, rl.ShaderAttributeDataType.SHADER_ATTRIB_VEC3)

        rl.set_shader_value(sun_shader, sun_u_view_pos, player.camera.position, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)
        rl.set_shader_value(sun_shader, sun_u_time, rl.get_time(), rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)


        rl.begin_texture_mode(target)
        rl.clear_background(BLACK)

        rl.begin_mode_3d(player.camera)

        rl.rl_disable_depth_mask()
        rl.draw_mesh_instanced(sky_model, sky_mat, sky_transforms, 1000)
        rl.rl_enable_depth_mask()

        rl.draw_mesh(sphere, sun_mat, system.bodies[0].transform)

        for planet in system.planets():
            planet_mat.maps.color = planet.color
            planet_mat.maps[MaterialMapIndex.MATERIAL_MAP_ALBEDO].texture = texture_types[planet.type]
            rl.draw_mesh(sphere, planet_mat, planet.transform)
        rl.end_mode_3d()

        # draw UI
        rl.draw_fps(10, 10)

        rl.draw_texture_pro(vaisseau, Rectangle(0, 0, 1280, 720),
                            Rectangle(0, 0, rl.get_render_width(), rl.get_render_height()), Vector2(0, 0), 0.0,
                            WHITE)

        if selected_planet != -1:
            # show the relative velocity between the player and the selected planet
            planet = system.bodies[selected_planet]
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

                # Draw thicker lines under first (outline)
                rl.draw_circle_v(p1, 3, BLACK)
                rl.draw_line_ex(p1, Vector2(p2.x, p1.y), 3, BLACK)
                rl.draw_line_ex(p1, Vector2(p1.x, p2.y), 3, BLACK)

                # Draw lines above
                rl.draw_line_v(p1, Vector2(p2.x, p1.y), WHITE)
                rl.draw_line_v(p1, Vector2(p1.x, p2.y), WHITE)

                # Draw the four corners
                radius = projected_radius + 20
                rl.draw_ring_lines(p1, radius, radius, 22.5, 22.5+45, 24, WHITE)
                rl.draw_ring_lines(p1, radius, radius, 112.5, 112.5+45, 24, WHITE)
                rl.draw_ring_lines(p1, radius, radius, 202.5, 202.5+45, 24, WHITE)
                rl.draw_ring_lines(p1, radius, radius, 292.5, 292.5+45, 24, WHITE)

                # Draw the text

                # if velocity points in the same direction as player->planet then velocity is positive, otherwise (points away), it's negative
                # forward speed is the orthogonal projection of velocity on position
                # which is the dot product divided by distance
                distance = rl.vector3_length(pos_diff)
                forward_speed = rl.vector_3dot_product(vel, pos_diff) / distance

                text_pos = rl.vector2_add(p1, Vector2(radius, -10))
                rl.draw_text("{:.1f} m".format(distance), int(text_pos.x), int(text_pos.y), 20, WHITE)
                rl.draw_text("{:.1f} m/s".format(forward_speed), int(text_pos.x), int(text_pos.y+20), 20, WHITE)

        rl.draw_line_v(Vector2(cx, cy - 6), Vector2(cx, cy + 6), WHITE)
        rl.draw_line_v(Vector2(cx - 6, cy), Vector2(cx + 6, cy), WHITE)

        rl.end_texture_mode()

        # draw target to screen
        rl.begin_drawing()
        rl.draw_texture_rec(target.texture, inverted_render_rect, Vector2(0, 0), WHITE)


        if paused:
            # rl.draw_rectangle(0, 0, rl.get_render_width(), rl.get_render_height(), Color(0, 0, 0, 28))
            rl.draw_rectangle_rounded(Rectangle(cx - 50, cy - 15, 100, 30), 0.5, 16, BLACK)
            rl.draw_rectangle_rounded_lines(Rectangle(cx - 50, cy - 15, 100, 30), 0.5, 16, 3, WHITE)
            pause_width = rl.measure_text("Paused", 20)
            rl.draw_text("Paused", int(cx - pause_width/2), int(cy-10), 20, WHITE)

        rl.end_drawing()


if __name__ == '__main__':
    main()
