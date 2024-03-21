from typing import Iterable, Self
from math import sqrt, cos, sin, pi
from random import randint
import itertools

import pyray as rl
from pyray import Color, Matrix, Vector3

from utils import vec3_zero

class Planet:
    pos: Vector3
    vel: Vector3 # instantaneous velocity
    orbit_radius: float
    orbit_angle: float
    orbit_center: Self | None
    color : list[Color]
    type : int 
    mass: float
    radius: float
    transform: Matrix

    def __init__(self, orbit_radius: float, orbit_center: Self | None, G: float, surface_gravity: float, radius: float):
        self.pos = vec3_zero()
        self.vel = vec3_zero()
        self.colors = [ 
            Color(rl.get_random_value(0, 250), rl.get_random_value(0, 250), rl.get_random_value(0, 250), 255) 
            for i in range(5)
        ]
        self.type = rl.get_random_value(0, 3)
        self.orbit_radius = orbit_radius
        self.orbit_angle = 0
        self.orbit_center = orbit_center
        self.mass = radius*radius*surface_gravity / G # set mass based on surface gravity
        self.radius = radius
        self.transform = rl.matrix_identity()
        self.seed = randint(0, 100000)
        self.perlin = rl.gen_image_perlin_noise(1500, 500, randint(0, 1000), randint(0, 1000), 20.0)
        self.texture = rl.load_texture_from_image(self.perlin)

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

        angular_speed = sqrt(G * (self.orbit_center.mass + self.mass) / (self.orbit_radius**3))
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

class System:
    def __init__(self, sun: Planet):
        self.bodies = [sun]
    
    def add(self, planet: Planet):
        """
        Adds a new planet to the system.
        Note that planets should be added "in order of orbit",
        that means, planets should be added first, then moons, then moons of moons, etc...
        """
        self.bodies.append(planet)

    def planets(self) -> Iterable[Planet]:
        """
        Returns an iterator over only the system's planets (without the sun)
        """
        return itertools.islice(self.bodies, 1, None)

    def update(self, G: float, dt: float):
        """Updates the solar system to its next position"""
        for body in self.bodies:
            body.orbit(G, dt)
            body.compute_transform()

class System:
    def __init__(self, sun: Planet):
        self.bodies = [sun]
    
    def add(self, planet: Planet):
        """
        Adds a new planet to the system.
        Note that planets should be added "in order of orbit",
        that means, planets should be added first, then moons, then moons of moons, etc...
        """
        self.bodies.append(planet)

    def planets(self) -> Iterable[Planet]:
        """
        Returns an iterator over only the system's planets (without the sun)
        """
        return itertools.islice(self.bodies, 1, None)

    def update(self, G: float, dt: float):
        """Updates the solar system to its next position"""
        for body in self.bodies:
            body.orbit(G, dt)
            body.compute_transform()

class New_system:
    G = 5

    def new_sys(self):
        system = System(Planet(0, None, self.G, 20, 250))

        nb_planet = randint(3,7)

        for i in range(nb_planet):
            radius = randint(40, 75)
            system.add(Planet(500 + randint(175, 250)*i, system.bodies[0], self.G, 0.075*radius//1, radius))

        for j in range(1, nb_planet +1):
            lune = randint(1, 100)
            if lune <= 25:
                radius = randint(12, 25)
                system.add(Planet(125, system.bodies[i], self.G, 0.075 * radius // 1, radius))
        return system