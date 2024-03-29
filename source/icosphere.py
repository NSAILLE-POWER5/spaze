from dataclasses import dataclass
from math import asin, atan2, pi, sqrt
from pyray import Mesh, Vector3, vector3_add, vector3_normalize, vector3_scale
from raylib import ffi
import pyray as rl

@dataclass
class SimpleMesh:
    vertices: list[Vector3]
    # faces with vertices indicated in counter-clockwise order
    faces: list[tuple[int, int, int]]

    def create_mesh(self) -> Mesh:
        """Create a raylib mesh from the given simple mesh"""

        # raylib uses unsigned shorts for indices
        assert(len(self.vertices) < 2**16)

        # create raylib mesh (copy python data to C memory buffers)
        vertices = ffi.cast("float *", rl.mem_alloc(len(self.vertices)*3*ffi.sizeof("float")))
        normals = ffi.cast("float *", rl.mem_alloc(len(self.vertices)*3*ffi.sizeof("float")))
        faces = ffi.cast("unsigned short *", rl.mem_alloc(len(self.faces)*3*ffi.sizeof("unsigned short")))

        for i, v in enumerate(self.vertices):
            vertices[i*3] = v.x
            vertices[i*3 + 1] = v.y
            vertices[i*3 + 2] = v.z

            # the normal is the same as the point's position since this is the unit sphere 
            normals[i*3] = v.x
            normals[i*3 + 1] = v.y
            normals[i*3 + 2] = v.z

        for i, (v0, v1, v2) in enumerate(self.faces):
            faces[i*3] = v0
            faces[i*3 + 1] = v1
            faces[i*3 + 2] = v2

        # see https://github.com/raysan5/raylib/blob/9a8d73e6c32514275a0ba53fe528bcb7c2693e27/src/raylib.h#L339
        mesh = Mesh(
            len(self.vertices),
            len(self.faces),
            vertices,
            ffi.NULL,
            ffi.NULL,
            normals,
            ffi.NULL,
            ffi.NULL,
            faces,
            ffi.NULL,
            ffi.NULL,
            ffi.NULL,
            ffi.NULL,
            0,
            ffi.NULL
        )
        rl.upload_mesh(mesh, False)
        return mesh

# returns a list of vertices and a list of faces
def gen_icosahedron() -> SimpleMesh:
    phi = (1 + sqrt(5)) / 2
    vertices = [
        Vector3(-1,  phi,  0),
        Vector3( 1,  phi,  0),
        Vector3(-1, -phi,  0),
        Vector3( 1, -phi,  0),

        Vector3( 0, -1,  phi),
        Vector3( 0,  1,  phi),
        Vector3( 0, -1, -phi),
        Vector3( 0,  1, -phi),

        Vector3( phi,  0, -1),
        Vector3( phi,  0,  1),
        Vector3(-phi,  0, -1),
        Vector3(-phi,  0,  1)
    ]
    faces = [
        # 5 faces around point 0
        (0, 11, 5),
        (0, 5, 1),
        (0, 1, 7),
        (0, 7, 10),
        (0, 10, 11),

        # 5 adjacent faces
        (1, 5, 9),
        (5, 11, 4),
        (11, 10, 2),
        (10, 7, 6),
        (7, 1, 8),

        # 5 faces around point 3
        (3, 9, 4),
        (3, 4, 2),
        (3, 2, 6),
        (3, 6, 8),
        (3, 8, 9),

        # 5 adjacent faces
        (4, 9, 5),
        (2, 4, 11),
        (6, 2, 10),
        (8, 6, 7),
        (9, 8, 1)
    ]
    return SimpleMesh(vertices, faces)

def midpoint(a: Vector3, b: Vector3) -> Vector3:
    # (a+b)/2
    return vector3_scale(vector3_add(a, b), 0.5)

def subdivide(ico: SimpleMesh):
    """Subdivide every triangle in the given icosahedron into 4 new triangles"""
    # map vertices to their index
    vertex_set = { v: i for i, v in enumerate(ico.vertices) }
    faces = []

    def add_vert(v: Vector3) -> int:
        if v not in vertex_set:
            idx = len(ico.vertices)
            ico.vertices.append(v)
            vertex_set[v] = idx
            return idx
        else:
            return vertex_set[v]

    # subdivide every triangle into 4 new triangle
    #
    #       v1                    v1
    #      /  \                  /  \
    #     /    \                /    \
    #    /      \      =>      b------a
    #   /        \            / \    / \
    #  /          \          /   \  /   \
    # v2-----------v0      v2-----c-----v0

    for v0, v1, v2 in ico.faces:
        p0 = ico.vertices[v0]
        p1 = ico.vertices[v1]
        p2 = ico.vertices[v2]

        a = add_vert(midpoint(p0, p1))
        b = add_vert(midpoint(p1, p2))
        c = add_vert(midpoint(p2, p0))

        # keep faces in counter-clockwise order
        faces.append((v0, a, c))
        faces.append((a, v1, b))
        faces.append((c, b, v2))
        faces.append((a, b, c))

    ico.faces = faces

def gen_icosphere(num: int) -> SimpleMesh:
    """
    Creates a unit icosphere mesh with the given number of subdivisions.
    Panics if the number of subdivisions is less or equal to 0.
    Use `create_mesh` on the resulting object to create a drawable raylib mesh.
    """
    assert(num > 0)

    current = gen_icosahedron()
    for _ in range(num):
        subdivide(current)
    
    # map icosahedron point to sphere
    for i in range(len(current.vertices)):
        current.vertices[i] = vector3_normalize(current.vertices[i])
    return current
