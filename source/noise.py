from pyray import RenderTexture, Texture, Vector2
import pyray as rl
from raylib import ffi

noise_shader = None

def generate_noise(size: tuple[int, int], scale: Vector2, pos: Vector2, octaves: int, frequency: float, amplitude: float, ridge: bool, invert: bool) -> RenderTexture:
    global noise_shader
    if noise_shader == None:
        noise_shader = rl.load_shader("source/shaders/noise_vert.glsl", "source/shaders/noise_frag.glsl")

    rl.set_shader_value(noise_shader, rl.get_shader_location(noise_shader, "scale"), scale, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC2)
    rl.set_shader_value(noise_shader, rl.get_shader_location(noise_shader, "pos"), pos, rl.ShaderUniformDataType.SHADER_UNIFORM_VEC2)
    rl.set_shader_value(noise_shader, rl.get_shader_location(noise_shader, "octaves"), ffi.new("int *", octaves), rl.ShaderUniformDataType.SHADER_UNIFORM_INT)
    rl.set_shader_value(noise_shader, rl.get_shader_location(noise_shader, "frequency"), ffi.new("float *", frequency), rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
    rl.set_shader_value(noise_shader, rl.get_shader_location(noise_shader, "amplitude"), ffi.new("float *", amplitude), rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
    rl.set_shader_value(noise_shader, rl.get_shader_location(noise_shader, "ridge"), ffi.new("int *", int(ridge)), rl.ShaderUniformDataType.SHADER_UNIFORM_INT)
    rl.set_shader_value(noise_shader, rl.get_shader_location(noise_shader, "invert"), ffi.new("int *", int(invert)), rl.ShaderUniformDataType.SHADER_UNIFORM_INT)

    print(f"CREATING NOISE TEXTURE [{size[0]}x{size[1]}]")

    render = rl.load_render_texture(size[0], size[1])
    rl.begin_texture_mode(render)
    rl.begin_shader_mode(noise_shader)

    rl.draw_rectangle(0, 0, size[0], size[1], rl.WHITE)

    rl.end_shader_mode()
    rl.end_texture_mode()

    return render
