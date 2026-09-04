# -*- coding: utf-8 -*-
"""星槎空岛 · 管线公共工具：随机、调色板、集合、命名、注册、合并。"""
import bpy, math, random, os, re
from mathutils import Vector, Euler

SEED = 412
R = random.Random(SEED)

def rr(a, b):
    """seeded uniform"""
    return R.uniform(a, b)

def ri(a, b):
    return R.randint(a, b)

def jitter(d):
    """角度抖动 转换">rad"""
    return R.uniform(-d, d)

# ---------------------------------------------------------------- 调色板（圣经统一色）
HEX = {
    # 石
    'sand':    (0xe8, 0xe4, 0xd8),   # 砂岩墙
    'white':   (0xf0, 0xec, 0xe0),   # 白石
    'slate':   (0x4a, 0x4a, 0x4a),   # 深石板
    'basalt':  (0x6f, 0x66, 0x60),   # 岩体
    'darkstone':(0x3a, 0x3a, 0x3a),  # 白板墙/磁石
    'grave':   (0xb8, 0xba, 0xb0),   # 墓碑
    # 院色
    'gold':    (0xe8, 0xb4, 0x5b),   # 晨辉
    'green':   (0x2f, 0x7d, 0x4a),   # 星语
    'copper':  (0xc9, 0x7a, 0x4a),   # 锤音
    'blue':    (0x4a, 0x9d, 0xc9),   # 海心
    'glaze_gold':  (0xda, 0xa9, 0x4e),
    'glaze_green': (0x2e, 0x6e, 0x45),
    'glaze_copper':(0xb3, 0x6a, 0x40),
    'glaze_blue':  (0x3a, 0x6f, 0x9a),
    # 贵金属
    'gold_metal':  (0xd9, 0xb4, 0x5b),
    'copper_metal':(0xc9, 0x7a, 0x4a),
    'bronze':      (0x8a, 0x6a, 0x4a),
    # 木与织物
    'wood':    (0xc8, 0xb8, 0xa0),
    'wood_dark':(0x8a, 0x74, 0x5c),
    'wood_grey':(0x6a, 0x5c, 0x4c),
    'cloth_white':(0xe0, 0xdc, 0xd0),
    # 植被
    'grass':   (0x4a, 0x6a, 0x35),
    'grass2':  (0x56, 0x7a, 0x40),
    'leaf':    (0x3f, 0x66, 0x2e),
    'leaf_gold':(0xc8, 0xa2, 0x4a),
    'moss':    (0x6a, 0x7a, 0x50),
    'pine':    (0x2e, 0x4a, 0x30),
    'vine':    (0x4a, 0x6e, 0x3a),
    'flower_gold':(0xe8, 0xd0, 0x70),
    'flower_white':(0xf0, 0xf0, 0xe8),
    'flower_blue':(0x8a, 0xb0, 0xd0),
    'flower_purple':(0x8a, 0x6a, 0xa8),  # 仅海心花圃
    # 光
    'crystal': (0xbf, 0xef, 0xff),   # 星辉色
    'window':  (0xff, 0xd9, 0xa0),   # 窗光
    'lamp':    (0xff, 0xc8, 0x80),
    'water':   (0x3a, 0x9d, 0xc0),
    # 特殊
    'rust':    (0x7a, 0x52, 0x3a),
    'snow':    (0xf0, 0xf2, 0xf4),
}

def hx(name):
    c = HEX[name]
    return '#%02x%02x%02x' % c

def srgb2lin(c):
    def f(u):
        u /= 255.0
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]))

def lin(name):
    return srgb2lin(HEX[name])

# ---------------------------------------------------------------- 集合与命名
def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c

_reg_colls = {}
def coll(key, name=None, parent=None):
    """按分区键取集合（缓存）"""
    if key not in _reg_colls:
        _reg_colls[key] = new_coll(name or key, parent)
    return _reg_colls[key]

_used_names = {}
def name(prefix, tag):
    """保证唯一命名（GLB 友好）"""
    n = f'{prefix}_{tag}'
    k = _used_names.get(n, 0)
    if k:
        n = f'{n}_{k:02d}'
    _used_names[n] = _used_names.get(n, 0) + 1
    return n

def link_obj(ob, ckey, prefix, tag):
    """创建后挂到分区集合，统一命名；返回对象"""
    ob.name = name(prefix, tag)
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll(ckey).objects.link(ob)
    return ob

def parent_to(ob, parent):
    ob.parent = parent

# ---------------------------------------------------------------- 场景工具
def activate(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob

def apply_mods(ob):
    activate(ob)
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)

def shade(ob, smooth=True, angle=40):
    activate(ob)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    except Exception:
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
    if not smooth:
        try:
            bpy.ops.object.shade_flat()
        except Exception:
            pass

def join(objs, name):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    activate(objs[0])
    for o in objs[1:]:
        o.select_set(True)
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    return ob

def move(ob, pos, rot=None, scale=None):
    ob.location = pos
    if rot is not None:
        ob.rotation_euler = Euler(rot, 'XYZ')
    if scale is not None:
        ob.scale = scale
    return ob

def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------- 顶点法线/色
def vcol(ob, amt=0.06, seed=7, band=None):
    """按对象空间位置做明度噪声（顶点色），供材质 'Attribute' 使用"""
    me = ob.data
    if not me.vertex_colors:
        me.vertex_colors.new(name='Col')
    vc = me.vertex_colors['Col']
    rnd = random.Random(seed)
    off = (rnd.random() * 10, rnd.random() * 10, rnd.random() * 10)
    for loop in me.loops:
        v = me.vertices[loop.vertex_index].co
        n = math.sin(v.x * 1.7 + off[0]) * math.sin(v.y * 1.9 + off[1]) * 0.5 + 0.5
        n = (n - 0.5) * amt + 1.0
        vc.data[loop.index].color = (n, n, n, 1.0)

def world_bounds(objs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for ob in objs:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    return mn, mx

# ---------------------------------------------------------------- 通用几何
def make_mesh(name, verts, faces, mat=None, coll_key=None, prefix=None, tag=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    if coll_key:
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll(coll_key).objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob

def obj_apply(ob, fn):
    """对网格顶点就地变换（本地坐标任意）"""
    for v in ob.data.vertices:
        fn(v)
    ob.data.update()

def tris(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)

def report_objs(objs, title=''):
    print(f'[QA] {title}: {len(objs)} objects')
