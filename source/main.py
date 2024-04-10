from math import inf, pi, log1p

import pyray as rl
from pyray import Rectangle, Vector2, Vector3
from cockpit import Cockpit

from icosphere import gen_icosphere
from map import Map
from shaders import PlanetMaterial, SunMaterial, WormholeEffect, WormholeMaterial
from sky import Sky
from utils import get_projected_sphere_radius, randf
from player import Player
from system import Planet, System, New_system
from colors import BLACK, WHITE

def get_viewed_planet(player: Player, sys: System) -> Planet | None:
    cx = rl.get_render_width()/2
    cy = rl.get_render_height()/2
    ray = rl.get_mouse_ray(Vector2(cx, cy), player.camera)

    closest_dist, closest = inf, None
    for planet in sys.bodies:
        # skip if we're looking away from the planet
        player_to_planet = rl.vector3_subtract(planet.pos, player.pos)
        if rl.vector_3dot_product(ray.direction, player_to_planet) < 0:
            continue

        coll = rl.get_ray_collision_sphere(ray, planet.pos, planet.radius)
        if coll.hit:
            dist = rl.vector3_length_sqr(player_to_planet)
            if dist < closest_dist:
                closest_dist = dist
                closest = planet
    return closest

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
    wormhole_effect = WormholeEffect()
    sun_mat = SunMaterial()

    cockpit = Cockpit()

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

    selected_planet = None

    def reset_system():
        nonlocal sys
        nonlocal selected_planet

        player.pos = Vector3(0, 0, -1300)
        player.vel = Vector3(5, 0, 0)

        selected_planet = None

        sys.unload()
        sys = system.new_sys()
        # randomize orbit angles
        for planet in sys.planets():
            planet.orbit_angle = randf() * 2 * pi

    target = rl.load_render_texture(1280, 720)
    rl.set_texture_wrap(target.texture, rl.TextureWrap.TEXTURE_WRAP_CLAMP)

    paused = True

    map = Map()

    ite = 0
    dead = False

    unpaused_time = 0.0

    wormholing = False
    wormhole_time = 0.0

    def collision_check():
        for planet in sys.bodies:
            if rl.vector_3distance_sqr(player.pos, planet.pos) <= planet.radius**2:
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
            map.toggle()

        if not paused:
            unpaused_time += dt

            sys.update(G, dt)
            player.apply_gravity(G, dt, sys.bodies)
            if not map.enabled:
                player.handle_mouse_input(dt)
            player.handle_keyboard_input()
            player.integrate(dt)
            player.sync_camera()

            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                viewed_planet = get_viewed_planet(player, sys)
                if viewed_planet == selected_planet:
                    selected_planet = None
                elif viewed_planet != None:
                    selected_planet = viewed_planet

            if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
                rl.enable_cursor()
                paused = True
        else:
            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                rl.disable_cursor()
                paused = False

        if not dead and collision_check():
            ite = 0
            dead = True
            paused = True

        # wormhole touched
        if not wormholing and rl.vector_3distance_sqr(player.pos, sys.wormhole_pos) < sys.wormhole_size**2:
            wormholing = True
            wormhole_time = 0.0

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

        cockpit.draw(player, sys, selected_planet)

        if selected_planet != None:
            planet = selected_planet

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

        if map.enabled:
            map.update(G, player, sys)
            map.draw(player, sys, sphere, wormhole_mat)
        else:
            rl.draw_texture_rec(target.texture, inverted_render_rect, Vector2(0, 0), WHITE)

        if paused:
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
                paused = False
                dead = False
        
        if wormholing:
            wormhole_effect.set_global_values(wormhole_time)
            wormhole_effect.draw()

            wormhole_time += dt

            # effect finished
            if wormhole_time >= 8.0:
                wormhole_time = 0.0
                wormholing = False
                reset_system()

        rl.end_drawing()
    rl.unload_music_stream(back_sound)


if __name__ == '__main__':
    main()
