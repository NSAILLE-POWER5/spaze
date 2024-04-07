from pyray import RenderTexture, Vector2, Vector3
import pyray as rl
from raylib import ffi

from utils import draw_rectangle_tex_coords

class NoiseShader:
    def __init__(self):
        self.shader = rl.load_shader("", "shaders/noise_frag.glsl")
        self.u_scale = rl.get_shader_location(self.shader, "scale")
        self.u_pos = rl.get_shader_location(self.shader, "pos")
        self.u_octaves = rl.get_shader_location(self.shader, "octaves")
        self.u_frequency = rl.get_shader_location(self.shader, "frequency")
        self.u_amplitude = rl.get_shader_location(self.shader, "amplitude")
        self.u_warp = rl.get_shader_location(self.shader, "warp")
        self.u_ridge = rl.get_shader_location(self.shader, "ridge")
        self.u_invert = rl.get_shader_location(self.shader, "invert")       

noise_shader: NoiseShader | None = None

def generate_noise(size: tuple[int, int], scale: Vector3, pos: Vector2, octaves: int, frequency: float, amplitude: float, warp: float, ridge: bool, invert: bool) -> RenderTexture:
    """Generate a spherically mapped noise texture"""

    global noise_shader
    if noise_shader == None:
        noise_shader = NoiseShader()

    rl.set_shader_value(noise_shader.shader, noise_shader.u_scale, scale, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC3)
    rl.set_shader_value(noise_shader.shader, noise_shader.u_pos, pos, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC2)
    rl.set_shader_value(noise_shader.shader, noise_shader.u_octaves, ffi.new("int *", octaves), rl.ShaderUniformDataType.SHADER_UNIFORM_INT)
    rl.set_shader_value(noise_shader.shader, noise_shader.u_frequency, ffi.new("float *", frequency), rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
    rl.set_shader_value(noise_shader.shader, noise_shader.u_amplitude, ffi.new("float *", amplitude), rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
    rl.set_shader_value(noise_shader.shader, noise_shader.u_warp, ffi.new("float *", warp), rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
    rl.set_shader_value(noise_shader.shader, noise_shader.u_ridge, ffi.new("int *", int(ridge)), rl.ShaderUniformDataType.SHADER_UNIFORM_INT)
    rl.set_shader_value(noise_shader.shader, noise_shader.u_invert, ffi.new("int *", int(invert)), rl.ShaderUniformDataType.SHADER_UNIFORM_INT)

    print(f"CREATING NOISE TEXTURE [{size[0]}x{size[1]}]")

    render = rl.load_render_texture(size[0], size[1])
    rl.begin_texture_mode(render)
    rl.begin_shader_mode(noise_shader.shader)

    draw_rectangle_tex_coords(0, 0, size[0], size[1])

    rl.end_shader_mode()
    rl.end_texture_mode()

    return render
