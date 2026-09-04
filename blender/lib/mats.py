# -*- coding: utf-8 -*-
"""材质工厂：所有材质统一从这里创建，登记 flat 色（供 GLB 降级导出）。
规范（见 bible/03 拾贰 & bible/06 B）：
  - 金 #d9b45b 只用于"最贵的光"（塔穹肋/檐边、星穗馆金穹、四院饰边）
  - 紫禁用于学院
"""
import bpy

_reg = {}          # name -> material
_flat = {}         # name -> (r,g,b,metallic,roughness,emission_rgb,emission_str)
_N = None          # noise gen

def _srgb2lin(c):
    def f(u):
        u /= 255.0
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]))

def _hex(hx):
    hx = hx.lstrip('#')
    return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))

def make(name, hx, rough=0.6, metal=0.0, emit_hx=None, emit_str=0.0,
         variation=0.05, bump=0.0, bump_scale=18.0, noise_scale=7.0,
         glaze=False):
    """创建程序化材质。variation 影响基色噪声幅度；bump 为浮雕强度。"""
    if name in _reg:
        return _reg[name]
    rgb = _hex(hx)
    lin = _srgb2lin(rgb)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (600, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (300, 0)
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    def set_in(nm, val):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = val

    set_in('Metallic', metal)
    set_in('Roughness', rough)
    set_in('IOR', 1.45)

    # --- 基色 ---
    base = (lin[0], lin[1], lin[2], 1.0)
    if variation > 0.001:
        tex = nt.nodes.new('ShaderNodeTexNoise'); tex.location = (-400, 200)
        tex.inputs['Scale'].default_value = noise_scale
        tex.inputs['Detail'].default_value = 3.0
        tex.inputs['Roughness'].default_value = 0.55
        ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-200, 200)
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.65
        lo = [max(0.0, c * (1.0 - variation * 1.6)) for c in lin]
        hi = [min(1.0, c * (1.0 + variation * 1.4)) for c in lin]
        ramp.color_ramp.elements[0].color = (lo[0], lo[1], lo[2], 1.0)
        ramp.color_ramp.elements[1].color = (hi[0], hi[1], hi[2], 1.0)
        nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    else:
        set_in('Base Color', base)

    # --- 粗糙度微变 ---
    if variation > 0.001:
        tex2 = nt.nodes.new('ShaderNodeTexNoise'); tex2.location = (-400, -100)
        tex2.inputs['Scale'].default_value = noise_scale * 2.1
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.location = (-200, -100)
        mr.inputs['From Min'].default_value = 0.0
        mr.inputs['From Max'].default_value = 1.0
        lo = max(0.02, rough - 0.12); hi = min(1.0, rough + 0.12)
        mr.inputs['To Min'].default_value = lo
        mr.inputs['To Max'].default_value = hi
        nt.links.new(tex2.outputs['Fac'], mr.inputs['Value'])
        nt.links.new(mr.outputs['Result'], bsdf.inputs['Roughness'])

    # --- 凹凸 ---
    if bump > 0.001:
        texb = nt.nodes.new('ShaderNodeTexNoise'); texb.location = (-400, -350)
        texb.inputs['Scale'].default_value = bump_scale
        texb.inputs['Detail'].default_value = 4.0
        bmp = nt.nodes.new('ShaderNodeBump'); bmp.location = (-150, -350)
        bmp.inputs['Strength'].default_value = bump
        nt.links.new(texb.outputs['Fac'], bmp.inputs['Height'])
        nt.links.new(bmp.outputs['Normal'], bsdf.inputs['Normal'])

    # --- 玻璃/釉面 ---
    if glaze:
        set_in('Coat Weight', 0.6)
        set_in('Coat Roughness', 0.12)
        set_in('Specular IOR Level', 0.6)

    # --- 自发光 ---
    ein = emit_hx or hx
    ecol = _srgb2lin(_hex(ein))
    if emit_str > 0.0:
        set_in('Emission Color', (ecol[0], ecol[1], ecol[2], 1.0))
        set_in('Emission Strength', emit_str)
    else:
        set_in('Emission Strength', 0.0)

    _reg[name] = mat
    _flat[name] = (lin, metal, rough, ecol, emit_str)
    return mat

def M(name):
    return _reg[name]

def flat(name):
    return _flat[name]

def flatten_all():
    """将程序化材质退化为纯色（节点断开，保留 Principled 直连值）——供 GLB 导出。"""
    for name, mat in _reg.items():
        pass  # GLTF 导出器会忽略无法保留的程序节点；我们另有纯色替换方案（见 export_glb 的 dual material 逻辑）

def build_all():
    """按建筑志 拾贰 表建立全部材质。"""
    # 石材
    make('sandstone', '#e8e4d8', rough=0.55, variation=0.07, bump=0.22, bump_scale=22)
    make('limestone', '#efe8d8', rough=0.5, variation=0.05, bump=0.12)
    make('slate', '#4a4a4a', rough=0.6, variation=0.06)
    make('basalt', '#6a6158', rough=1.0, variation=0.14, bump=0.5, bump_scale=8)
    make('dark_stone', '#3a3a3a', rough=0.7, variation=0.05)
    make('mountain_rock', '#7a6a58', rough=0.9, variation=0.09, bump=0.25, bump_scale=10)
    make('cobble', '#c4bcab', rough=0.78, variation=0.10, bump=0.3, bump_scale=10)
    make('plaza_dark', '#5a5a52', rough=0.75, variation=0.05)
    make('plaza_mid', '#8a8578', rough=0.75, variation=0.05)
    # 瓦
    make('tile_deep', '#54565a', rough=0.5, variation=0.06)
    make('tile_dawn', '#e8b45b', rough=0.35, metal=0.15, variation=0.04, glaze=True)
    make('tile_speak', '#2f7d4a', rough=0.35, metal=0.15, variation=0.04, glaze=True)
    make('tile_forge', '#c97a4a', rough=0.35, metal=0.15, variation=0.04, glaze=True)
    make('tile_tide', '#3a6f9a', rough=0.35, metal=0.15, variation=0.04, glaze=True)
    # 金属
    make('gold', '#d9b45b', rough=0.3, metal=0.85, variation=0.03)
    make('copperverde', '#4a8a7a', rough=0.45, metal=0.6, variation=0.05)
    make('iron', '#55504a', rough=0.6, metal=0.8, variation=0.05)
    make('bronze', '#8a6a3a', rough=0.45, metal=0.85, variation=0.04)
    # 光
    make('glass_warm', '#ffd9a0', rough=0.2, emit_hx='#ffcf8a', emit_str=2.8)
    make('glass_cool', '#d8ecff', rough=0.2, emit_hx='#bfe8ff', emit_str=1.8)
    make('crystal', '#bfefff', rough=0.15, emit_hx='#bfefff', emit_str=4.0, glaze=True)
    make('lantern', '#ffc87a', rough=0.3, emit_hx='#ffb85a', emit_str=3.0)
    # 木
    make('wood', '#c8b8a0', rough=0.7, variation=0.06, bump=0.2, bump_scale=20)
    make('wood_dark', '#8a6a4a', rough=0.75, variation=0.06)
    make('wood_beam', '#a89070', rough=0.7, variation=0.05)
    make('rope', '#b8a888', rough=0.9, variation=0.08)
    # 自然
    make('grass', '#44622f', rough=0.95, variation=0.16, bump=0.4, bump_scale=36)
    make('soil', '#4a3a2a', rough=1.0, variation=0.10)
    make('foliage', '#2f5a34', rough=0.9, variation=0.15, bump=0.3, bump_scale=24)
    make('foliage_light', '#3f7243', rough=0.9, variation=0.15, bump=0.3, bump_scale=24)
    make('foliage_autumn', '#c88a3a', rough=0.9, variation=0.14, bump=0.3, bump_scale=24)
    make('trunk', '#6b4a30', rough=0.9, variation=0.08, bump=0.3, bump_scale=16)
    make('flower_gold', '#e8c85a', rough=0.7, emit_hx='#e8c85a', emit_str=0.25)
    make('flower_white', '#e8e8e8', rough=0.7, emit_hx='#e8e8e8', emit_str=0.15)
    make('flower_blue', '#5a8ac9', rough=0.7, emit_hx='#5a8ac9', emit_str=0.2)
    make('flower_purple', '#7a5a9a', rough=0.7, emit_hx='#7a5a9a', emit_str=0.2)  # 仅海心院门圃
    # 水
    make('water', '#3a9dc0', rough=0.08, variation=0.02, glaze=True, emit_hx='#1a4a66', emit_str=0.25)
    # 布
    make('cloth_dawn', '#e8b45b', rough=0.8)
    make('cloth_speak', '#2f7d4a', rough=0.8)
    make('cloth_forge', '#c97a4a', rough=0.8)
    make('cloth_tide', '#4a9dc9', rough=0.8)
    make('cloth_white', '#e8e8e0', rough=0.8)
