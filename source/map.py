from copy import copy
import pyray as rl
from pyray import Mesh, Vector3
from colors import BLACK, RED, WHITE
from player import Player
from shaders import WormholeMaterial

from system import System

def copy_state(system: System, player: Player) -> tuple[System, Player]:
    """
    Creates a copy of the given system and player state (with all texture/graphics information shared),
    to allow simulating them at a different speed than the real-time simulation.
    """
    system_copy = System(system.bodies[0])
    system_copy.wormhole_pos = system.wormhole_pos
    system_copy.wormhole_size = system.wormhole_size
    system_copy.wormhole_transform = system.wormhole_transform

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

class Map:
    def __init__(self):
        self.isometric_cam = rl.Camera3D(
            Vector3(1200, 1200, 1200),
            Vector3(0, 0, 0),
            Vector3(0, 1, 0),
            1200*2,
            rl.CameraProjection.CAMERA_ORTHOGRAPHIC
        )

        self.enabled = False

        self.trace = []
        self.collided = False

    def toggle(self):
        self.enabled = not self.enabled

    def update(self, G: float, player: Player, sys: System):
        rl.update_camera(self.isometric_cam, rl.CameraMode.CAMERA_THIRD_PERSON)

        sys_copy, player_copy = copy_state(sys, player)

        simul_dt = 1/2
        self.trace = [player.pos]
        self.collided = False

        # simulate 50 seconds in advance
        for _ in range(100):
            sys_copy.update(G, simul_dt)
            player_copy.apply_gravity(G, simul_dt, sys_copy.bodies)
            player_copy.integrate(simul_dt)

            for body in sys_copy.bodies:
                if rl.vector_3distance_sqr(player_copy.pos, body.pos) < body.radius*body.radius:
                    self.collided = True
                    break

            if self.collided:
                break

            self.trace.append(player_copy.pos)

    def draw(self, player: Player, sys: System, sphere_mesh: Mesh, wormhole_mat: WormholeMaterial):
        rl.begin_mode_3d(self.isometric_cam)

        rl.clear_background(BLACK)
        for body in sys.bodies:
            if body.orbit_center != None:
                rl.draw_circle_3d(body.orbit_center.pos, body.orbit_radius, Vector3(1, 0, 0), 90, rl.fade(body.colors[3], 0.5))

            rl.draw_sphere(body.pos, body.radius, body.colors[3])
        rl.draw_mesh(sphere_mesh, wormhole_mat.mat, sys.wormhole_transform)

        for i in range(1, len(self.trace)):
            prev = self.trace[i-1]
            new = self.trace[i]
            rl.draw_line_3d(prev, new, WHITE)

        if len(self.trace) < 101:
            l = len(self.trace)-1
            rl.draw_sphere(self.trace[l], 10, RED)

        rl.draw_cube(rl.vector3_add(player.pos, Vector3(5, 5, 5)), 10, 10, 10, WHITE)

        rl.end_mode_3d()
