# -*- coding: utf-8 -*-
"""程序化可平铺贴图生成器（纯 numpy，无 bpy 依赖；可由系统 python3 运行）。
输出：assets/textures/*.png（512²，sRGB，可平铺）。
"""
import os, zlib, struct
import numpy as np

SZ = 512

# ---------------------------------------------------------------- PNG 编码（纯 zlib）
def write_png(path, rgb):
    """rgb: (H,W,3) uint8 或 float32 0..1 → RGBA PNG"""
    if rgb.dtype != np.uint8:
        rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    h, w, _ = rgb.shape
    a = np.full((h, w, 1), 255, np.uint8)
    raw = np.concatenate([rgb, a], axis=2)          # (h, w, 4)
    # 每行前置 1 个 filter byte (0 = None)——注意：每个 filter 只有 1 字节！
    row_len = w * 4
    rows = np.zeros((h, row_len + 1), np.uint8)
    rows[:, 1:] = raw.reshape(h, row_len)
    data = zlib.compress(rows.tobytes(), 6)

    def chunk(tag, payload):
        c = struct.pack('>I', len(payload)) + tag + payload
        return c + struct.pack('>I', zlib.crc32(tag + payload) & 0xffffffff)

    ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', data))
        f.write(chunk(b'IEND', b''))

def _img(path, rgb):
    write_png(path, rgb)
    return path

# ---------------------------------------------------------------- 噪声工具（可平铺）
def _wrap(N, seed):
    rng = np.random.default_rng(seed)
    grid = rng.random((N + 1, N + 1)).astype(np.float32)
    grid[-1, :] = grid[0, :]
    grid[:, -1] = grid[:, 0]
    return grid

def value_noise(N=SZ, scale=8, seed=1, octaves=3):
    total = np.zeros((N, N), np.float32)
    amp, freq, s = 1.0, scale, seed
    for o in range(octaves):
        g = _wrap(freq, s + o * 17)
        xs = np.linspace(0, freq, N, endpoint=False)
        xi = xs.astype(int); xf = xs - xi
        xf = xf * xf * (3 - 2 * xf)
        v = (g[np.ix_(xi, xi)] * (1 - xf)[:, None] * (1 - xf)[None, :] +
             g[np.ix_(xi + 1, xi)] * xf[:, None] * (1 - xf)[None, :] +
             g[np.ix_(xi, xi + 1)] * (1 - xf)[:, None] * xf[None, :] +
             g[np.ix_(xi + 1, xi + 1)] * xf[:, None] * xf[None, :])
        total += (v * amp).astype(np.float32)
        amp *= 0.5; freq *= 2
    total /= max(total.max(), 1e-6)
    return total.astype(np.float32)

def _mix(c1, c2, t):
    a = np.asarray(c1, np.float32)
    b = np.asarray(c2, np.float32)
    if a.ndim == 1:
        a = a / 255.0
    if b.ndim == 1:
        b = b / 255.0
    t = t.astype(np.float32)[..., None]
    return a * (1 - t) + b * t

# ---------------------------------------------------------------- 各贴图
def grass(seed=11):
    n = value_noise(scale=10, seed=seed, octaves=4)
    n2 = value_noise(scale=120, seed=seed + 3, octaves=2)
    base = _mix((0x4a, 0x6a, 0x35), (0x56, 0x7a, 0x40), n)
    base = _mix(base, (0x3c, 0x58, 0x2c), n2 * 0.5)
    return base

def dirt(seed=21):
    n = value_noise(scale=14, seed=seed, octaves=4)
    return _mix((0x5a, 0x4a, 0x3a), (0x44, 0x38, 0x2c), n)

def rock(seed=31, c1=(0x7a, 0x70, 0x68), c2=(0x62, 0x5a, 0x54)):
    n = value_noise(scale=9, seed=seed, octaves=5)
    base = _mix(c1, c2, n)
    cr = value_noise(scale=64, seed=seed + 5, octaves=2)
    base = _mix(base, (0x4a, 0x44, 0x40), (cr > 0.86) * 0.7)
    return base

def plaster(seed=41, c=(0xe8, 0xe4, 0xd8)):
    n = value_noise(scale=24, seed=seed, octaves=3)
    base = _mix(c, (0xd8, 0xd2, 0xc4), n * 0.5)
    sp = value_noise(scale=96, seed=seed + 2, octaves=2)
    base = _mix(base, (0xf4, 0xf0, 0xe4), (sp > 0.9) * 0.35)
    return base

def stonewall(seed=51, c=(0xe8, 0xe4, 0xd8), rows=6, cols=8, mortar=0.16):
    yy, xx = np.mgrid[0:SZ, 0:SZ].astype(np.float32)
    rh = SZ / rows
    row = np.floor(yy / rh).astype(np.int64)
    off = (row % 2) * (SZ / cols / 2)
    cw = SZ / cols
    cx = np.floor(((xx + off) % SZ) / cw).astype(np.int64)
    rng = np.random.default_rng(seed)
    tint = (rng.random((rows, cols + 2)) * 0.16).astype(np.float32)
    t = tint[row % rows, cx % (cols + 2)]
    base = _mix(c, (0xb8, 0xb2, 0xa6), t)
    fx = (xx + off) % cw
    fy = yy % rh
    edge = (fx < cw * mortar) | (fy < rh * mortar) | (fx > cw * (1 - mortar)) | (fy > rh * (1 - mortar))
    n = value_noise(scale=40, seed=seed + 7, octaves=2)
    base = base * ((0.82 + 0.18 * n)[..., None].astype(np.float32))
    base = _mix(base, (0x9a, 0x94, 0x8a), edge * 0.55)
    return base.astype(np.float32)

def slate(seed=61, c=(0x4a, 0x4a, 0x4a), rows=10):
    yy, xx = np.mgrid[0:SZ, 0:SZ].astype(np.float32)
    rh = SZ / rows
    row = np.floor(yy / rh).astype(np.int64)
    off = (row % 2) * 18.0
    cw = 3.0
    cell = (xx + off) % cw
    fy = yy % rh
    edge = fy < 2.2
    rng = np.random.default_rng(seed)
    tint = (rng.random(rows) * 0.14).astype(np.float32)
    t = (tint[row] * (0.4 + cell / cw)).astype(np.float32)
    base = _mix(c, (0x33, 0x33, 0x33), t)
    n = value_noise(scale=30, seed=seed + 3, octaves=2)
    base = base * ((0.85 + 0.15 * n)[..., None].astype(np.float32))
    base = _mix(base, (0x24, 0x24, 0x24), edge * 0.5)
    return base.astype(np.float32)

def glaze(seed=71, c=(0xda, 0xa9, 0x4e)):
    yy, xx = np.mgrid[0:SZ, 0:SZ].astype(np.float32)
    cw, rh = 32.0, 30.0
    cell = xx % cw
    fy = yy % rh
    edge = cell < 2.0
    drop = np.clip((fy / rh - 0.55) / 0.45, 0, 1)
    base = np.ones((SZ, SZ, 3), np.float32) * (np.array(c, np.float32) / 255.0)
    base = base * ((0.86 + 0.14 * value_noise(scale=24, seed=seed, octaves=2))[..., None].astype(np.float32))
    base = _mix(base, tuple(int(v * 0.62) for v in c), ((edge * 0.5 + drop * 0.28)).astype(np.float32))
    return base.astype(np.float32)

def plank(seed=81, c=(0xc8, 0xb8, 0xa0), planks=9):
    yy, xx = np.mgrid[0:SZ, 0:SZ].astype(np.float32)
    pw = SZ / planks
    px = np.floor(xx / pw).astype(np.int64)
    rng = np.random.default_rng(seed)
    tint = (rng.random(planks) * 0.24).astype(np.float32)
    base = _mix(c, (0x8a, 0x74, 0x5c), tint[px])
    grain = value_noise(scale=48, seed=seed + 5, octaves=2)
    base = base * ((0.9 + 0.1 * grain)[..., None].astype(np.float32))
    edge = (xx % pw) < 1.6
    base = _mix(base, (0x6a, 0x5c, 0x4c), edge * 0.5)
    return base.astype(np.float32)

def metal_weathered(seed=91, c=(0x4a, 0x8a, 0x7a), patina=(0x8a, 0xc0, 0xa8)):
    n = value_noise(scale=12, seed=seed, octaves=5)
    base = _mix(c, patina, np.clip((n - 0.45) * 2.2, 0, 1))
    scratch = value_noise(scale=150, seed=seed + 3, octaves=2)
    base = _mix(base, (0x2c, 0x50, 0x46), (scratch > 0.93) * 0.6)
    return base.astype(np.float32)

def brushed(seed=95, c=(0xd9, 0xb4, 0x5b)):
    n = value_noise(scale=8, seed=seed, octaves=3)
    base = _mix(c, (0xb8, 0x94, 0x42), n * 0.5)
    s = value_noise(scale=200, seed=seed + 2, octaves=1)
    base = base * ((0.94 + 0.06 * s)[..., None].astype(np.float32))
    return base.astype(np.float32)

def rust(seed=97, c=(0x7a, 0x52, 0x3a), rustc=(0x8a, 0x5a, 0x30)):
    n = value_noise(scale=10, seed=seed, octaves=5)
    base = _mix(c, (0x4c, 0x34, 0x26), n * 0.6)
    bl = value_noise(scale=5, seed=seed + 1, octaves=3)
    base = _mix(base, rustc, np.clip((bl - 0.5) * 2.0, 0, 1))
    return base.astype(np.float32)

def darkboard(seed=99):
    yy, xx = np.mgrid[0:SZ, 0:SZ].astype(np.float32)
    base = np.ones((SZ, SZ, 3), np.float32) * (np.array((0x3a, 0x3a, 0x3a), np.float32) / 255.0)
    n = value_noise(scale=20, seed=seed, octaves=3)
    base = base * ((0.85 + 0.15 * n)[..., None].astype(np.float32))
    for i in range(5):
        y0 = 60 + i * 90 + (seed % 7)
        ln = np.clip(1 - np.abs(yy - y0) / 3.0, 0, 1) * (0.10 + (i % 3) * 0.05)
        xmask = (np.sin(xx / 40.0 + i * 2.0) * 0.5 + 0.5) * ((yy > y0 - 8) & (yy < y0 + 14))
        base = base + ln[..., None] * xmask[..., None] * 0.35
    return base.astype(np.float32)

def bark(seed=101):
    n = value_noise(scale=6, seed=seed, octaves=4)
    xx = np.tile(np.linspace(0, 1, SZ, dtype=np.float32), (SZ, 1))
    base = _mix((0x6a, 0x54, 0x40), (0x50, 0x40, 0x34), n)
    strk = np.clip(np.sin(xx * 90 + n * 6) * 0.5 + 0.5, 0, 1)
    base = _mix(base, (0x44, 0x36, 0x2c), strk * 0.35)
    return base.astype(np.float32)

def street(seed=111, c=(0xcf, 0xc8, 0xb8)):
    yy, xx = np.mgrid[0:SZ, 0:SZ].astype(np.float32)
    cw = 64.0
    row = np.floor(yy / cw).astype(np.int64)
    off = (row % 2) * 32.0
    fx = (xx + off) % cw
    fy = yy % cw
    edge = (fx < 3) | (fy < 3) | (fx > cw - 3) | (fy > cw - 3)
    rng = np.random.default_rng(111)
    rid = (((xx + off) / cw).astype(np.int64) + row * 7) % 512
    tint = np.take((rng.random(512) * 0.2).astype(np.float32), rid, axis=0)
    base = _mix(c, (0xa8, 0xa0, 0x90), tint)
    n = value_noise(scale=30, seed=seed + 2, octaves=2)
    base = base * ((0.9 + 0.1 * n)[..., None].astype(np.float32))
    base = _mix(base, (0x8a, 0x84, 0x78), edge * 0.5)
    return base.astype(np.float32)

def water(seed=121):
    n = value_noise(scale=18, seed=seed, octaves=4)
    return _mix((0x3a, 0x9d, 0xc0), (0x2e, 0x7a, 0x9a), n * 0.8)

# ---------------------------------------------------------------- 构建
ITEMS = [
    ('grass_d', grass), ('dirt_d', dirt), ('rock_d', rock),
    ('rock2_d', lambda: rock(seed=33, c1=(0x6e, 0x66, 0x60), c2=(0x54, 0x4e, 0x4a))),
    ('plaster_d', plaster), ('plaster_w_d', lambda: plaster(seed=43, c=(0xf0, 0xec, 0xe0))),
    ('stonewall_d', stonewall), ('stonewall_w_d', lambda: stonewall(seed=53, c=(0xf0, 0xec, 0xe0))),
    ('slate_d', slate),
    ('glaze_gold_d', lambda: glaze(c=(0xda, 0xa9, 0x4e))),
    ('glaze_green_d', lambda: glaze(seed=72, c=(0x2e, 0x6e, 0x45))),
    ('glaze_copper_d', lambda: glaze(seed=73, c=(0xb3, 0x6a, 0x40))),
    ('glaze_blue_d', lambda: glaze(seed=74, c=(0x3a, 0x6f, 0x9a))),
    ('plank_d', plank), ('plank_dark_d', lambda: plank(seed=82, c=(0x8a, 0x74, 0x5c))),
    ('cuprite_d', metal_weathered), ('gold_d', brushed), ('rust_d', rust),
    ('darkboard_d', darkboard), ('bark_d', bark), ('street_d', street), ('water_d', water),
]

def build_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    for nm, fn in ITEMS:
        p = os.path.join(outdir, nm + '.png')
        _img(p, fn())
        print('[texgen]', nm)
    print('[texgen] done ->', outdir)

if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), 'assets', 'textures')
    build_all(out)
