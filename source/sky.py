import pyray as rl
from raylib import ffi
from shaders import SkyMaterial

from utils import randf

class Sky:
    def __init__(self):
        self.model = rl.gen_mesh_sphere(1, 4, 4)
        self.mat = SkyMaterial()

        # allocate an array of 1000 matrices
        self.transforms = ffi.cast("Matrix *", rl.mem_alloc(1000*ffi.sizeof("Matrix")))
        for i in range(1000):
            # bundle points closer to the horizon line
            y = (randf()*2-1)*(randf()*2-1)*(randf()*2-1)

            v = rl.Vector3(randf()*2 - 1, y, randf()*2 - 1)
            v = rl.vector3_scale(rl.vector3_normalize(v), 500)
            scale = randf() + 0.5
            self.transforms[i] = rl.matrix_multiply(rl.matrix_scale(scale, scale, scale), rl.matrix_translate(v.x, v.y, v.z))

    def draw(self):
        rl.rl_disable_depth_mask()
        rl.draw_mesh_instanced(self.model, self.mat.mat, self.transforms, 1000)
        rl.rl_enable_depth_mask()
