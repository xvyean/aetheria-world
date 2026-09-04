# -*- coding: utf-8 -*-
"""星槎学院 · 建模引擎 · 基础设施
Blender 4.2 · 程序化几何 Builder + 通用工具
"""
import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Euler
from mathutils import noise as mnoise

TAU = math.tau
PI = math.pi


# ---------------------------------------------------------------- 工具函数
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h, alpha=1.0):
    """'#RRGGBB' -> linear RGBA"""
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), alpha)


def M(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return Matrix.LocRotScale(Vector(loc), Euler(rot, 'XYZ'), Vector(scale))


# 别名（island/academy 模块中 M 用作材质字典）
MAT = M


def srand(seed):
    return random.Random(seed)


def vnoise(x, y=0.0, z=0.0, freq=1.0, seed=0.0):
    """确定性值噪声 [-1,1]，基于 mathutils.noise"""
    p = Vector((x * freq + seed * 13.7, y * freq + seed * 7.31, z * freq + seed * 3.9))
    return mnoise.noise(p)


def fbm(x, y, octaves=4, freq=1.0, seed=0.0, lac=2.0, gain=0.5):
    v, a, f, s = 0.0, 1.0, freq, seed
    for _ in range(octaves):
        v += a * vnoise(x, y, 0.0, f, s)
        f *= lac
        a *= gain
    return v


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def smoothstep(e0, e1, x):
    t = clamp((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- Builder
class B:
    """bmesh 累加器：一次构建一个对象，多材质槽按面分配。"""

    def __init__(self, name, mats):
        self.name = name
        self.bm = bmesh.new()
        self.mats = list(mats)
        self.slot = {m.name if hasattr(m, 'name') else m: i for i, m in enumerate(self.mats)}

    # ---- primitive helpers ----
    def _slot(self, mat):
        return self.slot[mat if isinstance(mat, str) else mat.name]

    def _finish(self, ret, mat, smooth):
        slots = self._slot(mat)
        faces = set()
        for v in ret['verts']:
            for f in v.link_faces:
                faces.add(f)
        for f in faces:
            f.material_index = slots
            f.smooth = smooth
        return ret

    def box(self, size, matrix, mat, smooth=False):
        ret = bmesh.ops.create_cube(self.bm, size=1.0, matrix=matrix @ M(scale=size))
        return self._finish(ret, mat, smooth)

    def cyl(self, r1, r2, depth, seg, matrix, mat, caps=True, smooth=True):
        ret = bmesh.ops.create_cone(self.bm, cap_ends=caps, cap_tris=False,
                                    segments=seg, radius1=r1, radius2=r2,
                                    depth=depth, matrix=matrix)
        return self._finish(ret, mat, smooth)

    def uvsph(self, r, matrix, mat, u=20, v=12, smooth=True):
        ret = bmesh.ops.create_uvsphere(self.bm, u_segments=u, v_segments=v,
                                        radius=r, matrix=matrix)
        return self._finish(ret, mat, smooth)

    def ico(self, r, subdiv, matrix, mat, smooth=False):
        ret = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv,
                                         radius=r, matrix=matrix)
        return self._finish(ret, mat, smooth)

    def grid(self, nx, ny, size_x, size_y, matrix, mat):
        ret = bmesh.ops.create_grid(self.bm, x_segments=nx, y_segments=ny,
                                    size=1.0, matrix=matrix @ M(scale=(size_x, size_y, 1)))
        return self._finish(ret, mat, False)

    def prism_xz(self, pts, thick, matrix, mat, smooth=False):
        """pts: [(x,z)...] 闭环轮廓，沿 Y 挤出 thick（居中）"""
        bm = self.bm
        front = [bm.verts.new(matrix @ Vector((x, -thick / 2, z))) for x, z in pts]
        back = [bm.verts.new(matrix @ Vector((x, thick / 2, z))) for x, z in pts]
        n = len(pts)
        faces = []
        try:
            f = bm.faces.new(front)
            faces.append(f)
        except ValueError:
            pass
        try:
            f = bm.faces.new(list(reversed(back)))
            faces.append(f)
        except ValueError:
            pass
        for i in range(n):
            a, b = front[i], front[(i + 1) % n]
            c, d = back[(i + 1) % n], back[i]
            faces.append(bm.faces.new((a, b, c, d)))
        self._assign_faces(faces, mat, smooth)
        return faces

    def arch_wall(self, w, h, thick, arch_r, segs, matrix, mat, smooth=False):
        """带半圆拱洞的墙（XZ 面轮廓，沿 Y 挤出）"""
        pts = []
        # 从左下角开始逆时针（从 -X 往 +X 看）
        pts.append((-w / 2, 0))
        pts.append((w / 2, 0))
        pts.append((w / 2, h))
        pts.append((arch_r, h))
        # 拱洞：右半圆 -> 左半圆（顺时针即轮廓向下凹）
        for i in range(segs + 1):
            a = -i * PI / segs
            pts.append((arch_r * math.cos(a), h + arch_r * math.sin(a) * 0.0 + arch_r * 0 + arch_r * math.sin(a)))
        for i in range(segs + 1):
            a = PI + i * PI / segs
            pts.append((arch_r * math.cos(a), arch_r * math.sin(a)))
        pts.append((-arch_r, h))
        pts.append((-w / 2, h))
        return self.prism_xz(pts, thick, matrix, mat, smooth)

    def torus(self, R, r, seg_u, seg_v, matrix, mat, smooth=True):
        bm = self.bm
        rings = []
        for i in range(seg_u):
            a = TAU * i / seg_u
            ring = []
            for j in range(seg_v):
                b = TAU * j / seg_v
                p = Vector(((R + r * math.cos(b)) * math.cos(a),
                            (R + r * math.cos(b)) * math.sin(a),
                            r * math.sin(b)))
                ring.append(bm.verts.new(matrix @ p))
            rings.append(ring)
        faces = []
        for i in range(seg_u):
            r0, r1 = rings[i], rings[(i + 1) % seg_u]
            for j in range(seg_v):
                faces.append(bm.faces.new((r0[j], r0[(j + 1) % seg_v],
                                           r1[(j + 1) % seg_v], r1[j])))
        self._assign_faces(faces, mat, smooth)
        return faces

    def ribbon(self, pts, widths, mat, up=Vector((0, 0, 1)), smooth=True):
        """沿折线 pts 的条带（用于河流/彩带）"""
        bm = self.bm
        left, right = [], []
        n = len(pts)
        for i in range(n):
            p = Vector(pts[i])
            if i == 0:
                d = (Vector(pts[1]) - p).normalized()
            elif i == n - 1:
                d = (p - Vector(pts[n - 2])).normalized()
            else:
                d = (Vector(pts[i + 1]) - Vector(pts[i - 1])).normalized()
            side = d.cross(up).normalized()
            w = widths[i] / 2
            left.append(bm.verts.new(p - side * w))
            right.append(bm.verts.new(p + side * w))
        faces = []
        for i in range(n - 1):
            faces.append(bm.faces.new((left[i], right[i], right[i + 1], left[i + 1])))
        self._assign_faces(faces, mat, smooth)
        return faces

    def loft(self, rings, mat, cap_start=True, cap_end=True, smooth=True):
        """rings: [ [Vector...], ... ] 等长环，闭合放样；cap 端为 ngon"""
        bm = self.bm
        vrings = [[bm.verts.new(p) for p in ring] for ring in rings]
        faces = []
        m = len(vrings[0])
        for a, b in zip(vrings, vrings[1:]):
            for i in range(m):
                faces.append(bm.faces.new((a[i], a[(i + 1) % m], b[(i + 1) % m], b[i])))
        if cap_start:
            faces.append(bm.faces.new(list(reversed(vrings[0]))))
        if cap_end:
            faces.append(bm.faces.new(vrings[-1]))
        self._assign_faces(faces, mat, smooth)
        return faces

    def _assign_faces(self, faces, mat, smooth):
        slots = self._slot(mat)
        for f in faces:
            try:
                f.material_index = slots
                f.smooth = smooth
            except ReferenceError:
                pass

    # ---- 输出 ----
    def to_object(self, collection=None, name=None):
        mesh = bpy.data.meshes.new(self.name + '_mesh')
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in self.mats:
            mesh.materials.append(m)
        obj = bpy.data.objects.new(name or self.name, mesh)
        (collection or bpy.context.scene.collection).objects.link(obj)
        return obj

    def to_mesh(self):
        mesh = bpy.data.meshes.new(self.name + '_mesh')
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in self.mats:
            mesh.materials.append(m)
        return mesh


def join_objects(objs, name):
    """合并对象（保留材质槽），返回新对象"""
    ctx = bpy.context
    for o in ctx.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    ctx.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = ctx.view_layer.objects.active
    joined.name = name
    return joined


def mesh_to_object(mesh, name, collection=None):
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def catenary(a, b, sag, n):
    """悬链点列"""
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = lerp(a, b, t)
        p.z -= sag * (4 * t * (1 - t))
        pts.append(p)
    return pts


def make_curve(points, bevel=0.05, mat=None, name='curve'):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = bevel
    cu.bevel_resolution = 2
    sp = cu.splines.new('POLY')
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
    obj = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(obj)
    if mat:
        cu.materials.append(mat)
    # 转为网格便于导出与保存
    ctx = bpy.context
    ctx.view_layer.objects.active = obj
    for o in ctx.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    obj = ctx.view_layer.objects.active
    return obj


def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block_list in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                       bpy.data.cameras, bpy.data.curves):
        for block in list(block_list):
            block_list.remove(block)
