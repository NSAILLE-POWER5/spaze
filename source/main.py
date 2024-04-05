from math import inf, pi, log1p, sqrt
from copy import copy

import pyray as rl
from pyray import Rectangle, Vector2, Vector3

from icosphere import gen_icosphere
from shaders import PlanetMaterial, SunMaterial, WormholeMaterial
from sky import Sky
from utils import get_projected_sphere_radius, randf
from player import Player
from system import System, New_system
from colors import BLACK, WHITE, RED, GREEN

def copy_state(system: System, player: Player) -> tuple[System, Player]:
    """
    Creates a copy of the given system and player state (with all texture/graphics information shared),
    to allow simulating them at a different speed than the real-time simulation.
    """
    system_copy = System(system.bodies[0])

    body_indices = { body: i for i, body in enumerate(system.bodies) }
    for planet in system.planets():
        p = copy(planet)
        p.orbit_center = None if planet.orbit_center == None else system_copy.bodies[body_indices[planet.orbit_center]]
        p.orbit_radius = planet.orbit_radius
        p.mass = planet.mass
        p.radius = planet.radius
        p.orbit_angle = planet.orbit_angle
        p.pos = planet.pos
        p.colors = planet.colors
        p.type = planet.type
        p.vel = planet.vel

        system_copy.add(p)

    player_copy = Player(
        player.pos,
        player.vel,
        player.camera,
        player.rotation,
        player.target_rotation
    )

    return system_copy, player_copy

def main():
    rl.init_window(1280, 720, "Spaze")
    rl.init_audio_device
    rl.set_target_fps(60)
    rl.set_window_state(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE)
    rl.set_exit_key(rl.KeyboardKey.KEY_NULL)

    G = 5
    dt = 1 / 60

    sphere = gen_icosphere(4).create_mesh()

    game_over = rl.load_texture("assets/game over.png")

    back_sound = rl.load_music_stream("assets/musique_de_fond.mp3")
    rl.play_music_stream(back_sound)

    planet_mat = PlanetMaterial()
    wormhole_mat = WormholeMaterial()
    sun_mat = SunMaterial()

    vaisseau = rl.load_texture("assets/cockpit.png")

    system = New_system()
    sys = system.new_sys()
    # initialize positions and transforms since the game is paused by default
    # and randomize orbit angles
    for planet in sys.planets():
        planet.orbit_angle = randf() * 2 * pi
    sys.update(G, dt)

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

    sky = Sky()

    def reset_system():
        nonlocal sys

        player.pos = Vector3(0, 0, -1300)
        player.vel = Vector3(5, 0, 0)

        sys.unload()
        sys = system.new_sys()
        # randomize orbit angles
        for planet in sys.planets():
            planet.orbit_angle = randf() * 2 * pi

    target = rl.load_render_texture(1280, 720)
    rl.set_texture_wrap(target.texture, rl.TextureWrap.TEXTURE_WRAP_CLAMP)

    selected_planet = -1

    paused = True

    map = False

    ite = 0
    dead = False

    unpaused_time = 0.0

    isometric_cam = rl.Camera3D(
        Vector3(1200, 1200, 1200),
        Vector3(0, 0, 0),
        Vector3(0, 1, 0),
        1200*2,
        rl.CameraProjection.CAMERA_ORTHOGRAPHIC
    )

    def CollisionCheck():
        for bodies in sys.bodies:
            if sqrt((player.pos.x - bodies.pos.x) ** 2 + (player.pos.y - bodies.pos.y) ** 2 + (player.pos.z - bodies.pos.z) ** 2) <= planet.radius:
                return True
        return False

    while not rl.window_should_close():
        rl.update_music_stream(back_sound)
        
        inverted_render_rect = Rectangle(0, 0, rl.get_render_width(), -rl.get_render_height())
        if rl.is_window_resized():
            rl.unload_render_texture(target)

            target = rl.load_render_texture(rl.get_render_width(), rl.get_render_height())
            rl.set_texture_wrap(target.texture, rl.TextureWrap.TEXTURE_WRAP_CLAMP)

        cx = rl.get_render_width()/2
        cy = rl.get_render_height()/2

        if rl.is_key_pressed(rl.KeyboardKey.KEY_SEMICOLON):
            map = not map

        if not paused:
            unpaused_time += dt

            sys.update(G, dt)
            player.apply_gravity(G, dt, sys.bodies)
            if not map:
                player.handle_mouse_input(dt)
            player.handle_keyboard_input()
            player.integrate(dt)
            player.sync_camera()

            if CollisionCheck():
                ite = 0
                dead = True
                paused = True

            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                closest, closest_idx = inf, None

                ray = rl.get_mouse_ray(Vector2(cx, cy), player.camera)
                for i, planet in enumerate(sys.bodies):
                    # skip if we're looking away from the planet
                    player_to_planet = rl.vector3_subtract(planet.pos, player.pos)
                    if rl.vector_3dot_product(ray.direction, player_to_planet) < 0:
                        continue

                    coll = rl.get_ray_collision_sphere(ray, planet.pos, planet.radius)
                    if coll.hit:
                        dist = rl.vector3_length_sqr(player_to_planet)
                        if dist < closest:
                            closest = dist
                            closest_idx = i

                if closest_idx == selected_planet:
                    selected_planet = -1
                elif closest_idx != None:
                    selected_planet = closest_idx

            if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
                rl.enable_cursor()
                paused = True
        else:
            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                rl.disable_cursor()
                paused = False

        if rl.vector_3distance_sqr(player.pos, sys.wormhole_pos) < sys.wormhole_size**2:
            # wormhole touched
            reset_system()

        planet_mat.set_global_values(player, sys)
        sun_mat.set_global_values(player, unpaused_time)
        wormhole_mat.set_global_values(unpaused_time)

        rl.begin_texture_mode(target)
        rl.clear_background(BLACK)

        rl.begin_mode_3d(player.camera)

        sky.draw()

        rl.draw_mesh(sphere, sun_mat.mat, sys.bodies[0].transform)
        for planet in sys.planets():
            planet_mat.set_planet_values(planet)
            rl.draw_mesh(sphere, planet_mat.mat, planet.transform) #ICI

        # draw wormhole
        rl.draw_mesh(sphere, wormhole_mat.mat, sys.wormhole_transform)

        rl.end_mode_3d()

        # draw UI
        rl.draw_fps(10, 10)

        rl.draw_texture_pro(vaisseau, Rectangle(0, 0, 1280, 720),
                            Rectangle(0, 0, rl.get_render_width(), rl.get_render_height()), Vector2(0, 0), 0.0,
                            WHITE)

        eau = 0
        oxy = 0
        temp = 0

        if selected_planet != -1:
            planet = sys.bodies[selected_planet]
            if sqrt((player.pos.x - planet.pos.x) ** 2 + (player.pos.y - planet.pos.y) ** 2 + (player.pos.z - planet.pos.z) ** 2) <= planet.radius + 250:
                if selected_planet == 0:
                    eau = 0
                    oxy = 0
                    temp = 15000
                else:
                    eau = planet.eau
                    oxy = planet.oxygen
                    temp = planet.temp

            eau_txt = str(eau) + "% H²0"
            water_width = rl.measure_text(eau_txt, 20)
            rl.draw_text(eau_txt, int(2*cx / 2.294 - (water_width / 2)), int(2*cy / 1.58), 20, GREEN)
            oxy_txt = str(oxy) + "% de O²"
            oxy_width = rl.measure_text(oxy_txt, 20)
            rl.draw_text(oxy_txt, int(2*cx / 2.006 - (oxy_width / 2)), int(2*cy / 1.38), 20, GREEN)
            temp_txt = str(temp) + " C°"
            temp_width = rl.measure_text(temp_txt, 20)
            rl.draw_text(temp_txt, int(2*cx / 1.778 - (temp_width / 2)), int(2*cy / 1.58), 20, GREEN)

            # show the relative velocity between the player and the selected planet
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

        if not map:
            rl.draw_texture_rec(target.texture, inverted_render_rect, Vector2(0, 0), WHITE)
        else:
            rl.update_camera(isometric_cam, rl.CameraMode.CAMERA_THIRD_PERSON)

            rl.begin_mode_3d(isometric_cam)

            rl.clear_background(BLACK)
            for body in sys.bodies:
                if body.orbit_center != None:
                    rl.draw_circle_3d(body.orbit_center.pos, body.orbit_radius, Vector3(1, 0, 0), 90, rl.fade(body.colors[0], 0.5))

                rl.draw_sphere(body.pos, body.radius, body.colors[0])
            rl.draw_mesh(sphere, wormhole_mat.mat, sys.wormhole_transform)

            system_copy, player_copy = copy_state(sys, player)

            simul_dt = 1/2
            trace = [player.pos]

            # simulate 50 seconds in advance
            for _ in range(100):
                system_copy.update(G, simul_dt)
                player_copy.apply_gravity(G, simul_dt, system_copy.bodies)
                player_copy.integrate(simul_dt)

                # check for collision
                stop = False
                for body in system_copy.bodies:
                    if rl.vector_3distance_sqr(player_copy.pos, body.pos) < body.radius*body.radius:
                        stop = True
                        break
                if stop:
                    break

                trace.append(player_copy.pos)


            for i in range(1, len(trace)):
                prev = trace[i-1]
                new = trace[i]
                rl.draw_line_3d(prev, new, WHITE)

            if len(trace) < 101:
                l = len(trace)-1
                rl.draw_sphere(trace[l], 10, RED)

            rl.draw_cube(rl.vector3_add(player.pos, Vector3(5, 5, 5)), 10, 10, 10, WHITE)


            rl.end_mode_3d()

        if paused:
            # rl.draw_rectangle(0, 0, rl.get_render_width(), rl.get_render_height(), Color(0, 0, 0, 28))
            rl.draw_rectangle_rounded(Rectangle(cx - 50, cy - 15, 100, 30), 0.5, 16, BLACK)
            rl.draw_rectangle_rounded_lines(Rectangle(cx - 50, cy - 15, 100, 30), 0.5, 16, 3, WHITE)
            pause_width = rl.measure_text("Paused", 20)
            rl.draw_text("Paused", int(cx - pause_width/2), int(cy-10), 20, WHITE)

        if dead:
            if ite < 300:
                rl.draw_texture_pro(game_over, Rectangle(0, 0, 1280, 720),
                                    Rectangle(0, 0, rl.get_render_width(), rl.get_render_height()), Vector2(0, 0), 0.0,
                                    WHITE)
                ite += 1
            else:
                reset_system()
                dead = False
        rl.end_drawing()
    rl.unload_music_stream(back_sound)


if __name__ == '__main__':
    main()
