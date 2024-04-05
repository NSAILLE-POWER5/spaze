import pyray as rl
from raylib import MATERIAL_MAP_ALBEDO, SHADER_ATTRIB_VEC3, SHADER_LOC_MATRIX_MODEL, SHADER_UNIFORM_FLOAT, SHADER_UNIFORM_VEC3, SHADER_UNIFORM_VEC4, ffi

from player import Player
from system import Planet, System

class PlanetMaterial:
    def __init__(self):
        self.shader = rl.load_shader("shaders/planet_vert.glsl", "shaders/planet_frag.glsl")
        self.u_ambient = rl.get_shader_location(self.shader, "ambient")
        self.u_sun_pos = rl.get_shader_location(self.shader, "sunPos")
        self.u_view_pos = rl.get_shader_location(self.shader, "viewPos")
        self.u_first_layer = rl.get_shader_location(self.shader, "first_layer")
        self.u_second_layer = rl.get_shader_location(self.shader, "second_layer")
        self.u_third_layer = rl.get_shader_location(self.shader, "third_layer")
        self.u_fourth_layer = rl.get_shader_location(self.shader, "fourth_layer")
        self.u_fifth_layer = rl.get_shader_location(self.shader, "fifth_layer")

        rl.set_shader_value(self.shader, self.u_ambient, rl.Vector4(0.1, 0.1, 0.1, 1.0), SHADER_UNIFORM_VEC4)
        self.shader.locs[rl.ShaderLocationIndex.SHADER_LOC_VECTOR_VIEW] = self.u_view_pos

        self.mat = rl.load_material_default()
        self.mat.shader = self.shader

    def set_planet_values(self, planet: Planet):
        self.mat.maps[MATERIAL_MAP_ALBEDO].texture = planet.noise.texture
        rl.set_shader_value(self.shader, self.u_first_layer, rl.Vector4(planet.colors[0].r / 255.0, planet.colors[0].g / 255.0, planet.colors[0].b / 255.0, planet.colors[0].a / 255.0), SHADER_UNIFORM_VEC4)
        rl.set_shader_value(self.shader, self.u_second_layer, rl.Vector4(planet.colors[1].r / 255.0, planet.colors[1].g / 255.0, planet.colors[1].b / 255.0, planet.colors[1].a / 255.0), SHADER_UNIFORM_VEC4)
        rl.set_shader_value(self.shader, self.u_third_layer, rl.Vector4(planet.colors[2].r / 255.0, planet.colors[2].g / 255.0, planet.colors[2].b / 255.0, planet.colors[2].a / 255.0), SHADER_UNIFORM_VEC4)
        rl.set_shader_value(self.shader, self.u_fourth_layer, rl.Vector4(planet.colors[3].r / 255.0, planet.colors[3].g / 255.0, planet.colors[3].b / 255.0, planet.colors[3].a / 255.0), SHADER_UNIFORM_VEC4)
        rl.set_shader_value(self.shader, self.u_fifth_layer, rl.Vector4(planet.colors[4].r / 255.0, planet.colors[4].g / 255.0, planet.colors[4].b / 255.0, planet.colors[4].a / 255.0), SHADER_UNIFORM_VEC4)

    def set_global_values(self, player: Player, sys: System):
        rl.set_shader_value(self.shader, self.u_view_pos, player.camera.position, SHADER_UNIFORM_VEC3)
        rl.set_shader_value(self.shader, self.u_sun_pos, sys.bodies[0].pos, SHADER_ATTRIB_VEC3)

class SunMaterial:
    def __init__(self):
        self.shader = rl.load_shader("shaders/sun_vert.glsl", "shaders/sun_frag.glsl")
        self.u_view_pos = rl.get_shader_location(self.shader, "viewPos")
        self.u_time = rl.get_shader_location(self.shader, "time")

        self.sun_texture = rl.load_texture("assets/sun.png")

        self.mat = rl.load_material_default()
        self.mat.maps[MATERIAL_MAP_ALBEDO].texture = self.sun_texture
        self.mat.maps[MATERIAL_MAP_ALBEDO].color = rl.Color(255, 210, 0, 255)
        self.mat.shader = self.shader

    def set_global_values(self, player: Player, unpaused_time: float):
        rl.set_shader_value(self.shader, self.u_view_pos, player.camera.position, SHADER_UNIFORM_VEC3)
        rl.set_shader_value(self.shader, self.u_time, ffi.new("float *", unpaused_time), SHADER_UNIFORM_FLOAT)

class WormholeMaterial:
    def __init__(self):
        self.shader = rl.load_shader("shaders/planet_vert.glsl", "shaders/wormhole_frag.glsl")
        self.u_time = rl.get_shader_location(self.shader, "time")

        self.mat = rl.load_material_default()
        self.mat.shader = self.shader

    def set_global_values(self, unpaused_time: float):
        rl.set_shader_value(self.shader, self.u_time, ffi.new("float *", unpaused_time), SHADER_UNIFORM_FLOAT)

class SkyMaterial:
    def __init__(self):
        self.shader = rl.load_shader("shaders/sky_vert.glsl", "shaders/sky_frag.glsl")
        self.shader.locs[SHADER_LOC_MATRIX_MODEL] = rl.get_shader_location_attrib(self.shader, "matModel")

        self.mat = rl.load_material_default()
        self.mat.shader = self.shader

