# -*- coding: utf-8 -*-
"""材质工厂：贴图 + Principled + 自发光。颜色以圣经《建筑志 v2》拾肆为准。
GLB 兼容：只用图像纹理 + 常量，不依赖程序化节点（bump 仅渲染增强）。
"""
import bpy, os
from mathutils import Vector
from . import util

_reg = {}
TEX = {}          # name -> png path
TEXDIR = None

# spec: (tex_key, rough, metal, tint_hex, emit_hex, emit_str, bump)
SPECS = {
    'stone_smooth': ('plaster_d', 0.55, 0.0, (0xec, 0xe8, 0xdc), None, 0, 0.04),
    'white_smooth': ('plaster_w_d', 0.48, 0.0, None, None, 0, 0.03),
    'grass':      ('grass_d', 0.80, 0.0, None, None, 0, 0.10),
    'dirt':       ('dirt_d', 0.95, 0.0, None, None, 0, 0.08),
    'rock':       ('rock_d', 0.90, 0.0, None, None, 0, 0.22),
    'rock2':      ('rock2_d', 1.0, 0.0, None, None, 0, 0.22),
    'plaster':    ('plaster_d', 0.55, 0.0, (0xe0, 0xdc, 0xd0), None, 0, 0.05),
    'plaster_w':  ('plaster_w_d', 0.55, 0.0, None, None, 0, 0.05),
    'stonewall':  ('plaster_d', 0.55, 0.0, (0xd8, 0xd3, 0xc6), None, 0, 0.05),
    'stonewall_l':('plaster_d', 0.50, 0.0, (0xe2, 0xdd, 0xd0), None, 0, 0.04),
    'stonewall_w':('plaster_w_d', 0.48, 0.0, None, None, 0, 0.04),
    'slate':      ('slate_d', 0.55, 0.0, (0x6a, 0x6a, 0x6a), None, 0, 0.10),
    'glaze_gold': ('glaze_gold_d', 0.35, 0.12, None, None, 0, 0.04),
    'glaze_green':('glaze_green_d', 0.35, 0.12, None, None, 0, 0.04),
    'glaze_copper':('glaze_copper_d', 0.35, 0.12, None, None, 0, 0.04),
    'glaze_blue': ('glaze_blue_d', 0.35, 0.12, None, None, 0, 0.04),
    'plank':      ('plank_d', 0.70, 0.0, None, None, 0, 0.05),
    'plank_dark': ('plank_dark_d', 0.75, 0.0, None, None, 0, 0.05),
    'cuprite':    ('cuprite_d', 0.42, 0.55, None, None, 0, 0.05),
    'gold':       ('gold_d', 0.30, 0.90, None, None, 0, 0.02),
    'bronze':     ('gold_d', 0.45, 0.80, (0x8a, 0x6a, 0x4a), None, 0, 0.02),
    'copper_metal': ('gold_d', 0.40, 0.80, (0xc9, 0x7a, 0x4a), None, 0, 0.02),
    'wood_dark':  ('plank_dark_d', 0.78, 0.0, None, None, 0, 0.05),
    'rust':       ('rust_d', 0.80, 0.30, None, None, 0, 0.06),
    'darkboard':  ('darkboard_d', 0.50, 0.0, None, None, 0, 0.0),
    'bark':       ('bark_d', 0.85, 0.0, None, None, 0, 0.12),
    'street':     ('street_d', 0.72, 0.0, (0xd0, 0xca, 0xbc), None, 0, 0.06),
    'water':      (None, 0.05, 0.0, (0x3a, 0x9d, 0xc0), None, 0, 0.0),
    'water_sea':  (None, 0.25, 0.0, (0x14, 0x24, 0x32), None, 0, 0.0),
    'crystal':    (None, 0.2, 0.0, (0xbf, 0xef, 0xff), (0xbf, 0xef, 0xff), 6.0, 0.0),
    'window':     (None, 0.3, 0.0, (0xff, 0xd9, 0xa0), (0xff, 0xd9, 0xa0), 2.0, 0.0),
    'lamp':       (None, 0.3, 0.0, (0xff, 0xc8, 0x80), (0xff, 0xc8, 0x80), 3.0, 0.0),
    'leaf':       (None, 0.75, 0.0, (0x4e, 0x78, 0x38), None, 0, 0.0),
    'leaf_gold':  (None, 0.8, 0.0, (0xc8, 0xa2, 0x4a), None, 0, 0.0),
    'pine':       (None, 0.75, 0.0, (0x3a, 0x58, 0x3c), None, 0, 0.0),
    'vine':       (None, 0.72, 0.0, (0x56, 0x78, 0x42), None, 0, 0.0),
    'moss':       (None, 0.85, 0.0, (0x76, 0x88, 0x58), None, 0, 0.0),
    'flower_gold':(None, 0.7, 0.0, (0xe8, 0xd0, 0x70), None, 0, 0.0),
    'flower_white':(None, 0.7, 0.0, (0xf0, 0xf0, 0xe8), None, 0, 0.0),
    'flower_blue':(None, 0.7, 0.0, (0x8a, 0xb0, 0xd0), None, 0, 0.0),
    'flower_purple':(None, 0.7, 0.0, (0x8a, 0x6a, 0xa8), None, 0, 0.0),  # 仅海心花圃
    'cloth':      (None, 0.9, 0.0, (0xe0, 0xdc, 0xd0), None, 0, 0.0),
    'cloth_grey': (None, 0.9, 0.0, (0xb0, 0xae, 0xa8), None, 0, 0.0),
    'cloth_white': (None, 0.9, 0.0, (0xf0, 0xf0, 0xe8), None, 0, 0.0),
    'blackstone': (None, 0.6, 0.0, (0x2e, 0x2e, 0x30), None, 0, 0.0),
    'grave':      ('plaster_w_d', 0.65, 0.0, (0xbe, 0xc0, 0xb6), None, 0, 0.05),
    'bell':       ('rust_d', 0.6, 0.6, None, None, 0, 0.0),
    'column':     ('plaster_w_d', 0.42, 0.0, None, None, 0, 0.03),
    'paper':      (None, 0.9, 0.0, (0xe8, 0xe2, 0xd2), None, 0, 0.0),
    'chalk':      (None, 0.9, 0.0, (0xf0, 0xf0, 0xe8), None, 0, 0.0),
    'iron':       (None, 0.5, 0.7, (0x4a, 0x4a, 0x50), None, 0, 0.0),
    'flag_gold':  (None, 0.8, 0.0, (0xe8, 0xb4, 0x5b), None, 0, 0.0),
    'flag_green': (None, 0.8, 0.0, (0x2f, 0x7d, 0x4a), None, 0, 0.0),
    'flag_copper':(None, 0.8, 0.0, (0xc9, 0x7a, 0x4a), None, 0, 0.0),
    'flag_blue':  (None, 0.8, 0.0, (0x4a, 0x9d, 0xc9), None, 0, 0.0),
    'smoke_stain':(None, 0.9, 0.0, (0x2a, 0x2a, 0x2c), None, 0, 0.0),
    'rope':       ('plank_dark_d', 0.9, 0.0, None, None, 0, 0.0),
    'foundation': ('street_d', 0.9, 0.0, None, None, 0, 0.0),
}

def init(texture_dir):
    """贴图由 tools/gen_textures.py 预生成（texgen.py，纯 numpy）；这里只记录目录。
    缺贴图时材质回退纯色（GLB 仍可用）。"""
    global TEXDIR, TEX
    TEXDIR = texture_dir
    TEX = {k.replace('.png', ''): k for k in os.listdir(texture_dir)} if os.path.isdir(texture_dir) else {}

def _srgb2lin(c):
    def f(u):
        u /= 255.0
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]))

def M(key):
    if key in _reg:
        return _reg[key]
    spec = SPECS[key]
    tex, rough, metal, tint, emit, estr, bump = spec
    mat = bpy.data.materials.new('M_' + key)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (700, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (380, 0)
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    def setp(nm, val):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = val

    setp('Roughness', rough)
    setp('Metallic', metal)
    setp('IOR', 1.45)

    if tex:
        img = bpy.data.images.load(os.path.join(TEXDIR, TEX[tex]), check_existing=False)
        img.colorspace_settings.name = 'sRGB'
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.location = (-520, 200)
        tn.image = img
        if tint:
            mix = nt.nodes.new('ShaderNodeMix'); mix.location = (-120, 200)
            mix.data_type = 'RGBA'
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            tc = _srgb2lin(tint)
            mix.inputs[6].default_value = (*tc, 1.0)   # A
            nt.links.new(tn.outputs['Color'], mix.inputs[7])  # B
            nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
        else:
            nt.links.new(tn.outputs['Color'], bsdf.inputs['Base Color'])
        if bump > 0.001:
            bn = nt.nodes.new('ShaderNodeTexNoise'); bn.location = (-520, -160)
            bn.inputs['Scale'].default_value = 22.0
            bn.inputs['Detail'].default_value = 6.0
            bm = nt.nodes.new('ShaderNodeBump'); bm.location = (-140, -160)
            bm.inputs['Strength'].default_value = bump
            nt.links.new(bn.outputs['Fac'], bm.inputs['Height'])
            nt.links.new(bm.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        base = _srgb2lin(tint or (0x80, 0x80, 0x80))
        setp('Base Color', (*base, 1.0))

    if emit:
        e = _srgb2lin(emit)
        setp('Emission Color', (*e, 1.0))
        setp('Emission Strength', estr)

    _reg[key] = mat
    return mat

def reset():
    _reg.clear()
