/* ============================================================
 * 艾瑟兰 · 地形系统 v3
 * 三块大陆（艾瑟兰主大陆 / 暮影大陆 / 铜脊大陆）+ 碎浪群岛 + 礁岛
 * 河流（水力追踪 / 指定流域）/ 湖泊 / 城市选址
 * 浏览器（window.Terrain）与 Node（module.exports）通用
 * ============================================================ */

(function (global) {
  'use strict';

  var N = global.Noise;
  var SIZE = 1600, SEG = 480, GRID = SEG + 1;
  var H = null;
  var riverMask = null;
  var lakeMask = null;
  var citySites = [];
  var riverPaths = [];
  var lakes = [];

  function configure(size, seg) {
    SIZE = size; SEG = seg; GRID = seg + 1;
  }

  /* ---------------- 大陆掩膜 ----------------
   * 主大陆沿用 v2 设计，坐标映射：old -> new: new = old * 0.72 + shift
   * shift = (-211, -7)；即 old = ((x+211)/0.72, (z-7)/0.72) */

  var SHIFT_X = -211, SHIFT_Z = -7, SCALE = 0.72;
  function toOld(x, z) { return { x: (x - SHIFT_X) / SCALE, z: (z - SHIFT_Z) / SCALE }; }

  // 主大陆掩膜（旧设计：扰动椭圆 + 西部荒原半岛）
  function mainMask(ox, oz) {
    var ex = (ox + 40) / 430, ez = (oz + 10) / 400;
    var d = Math.hypot(ex, ez);
    var wob = N.fbm(ox * 0.0016 + 31.7, oz * 0.0016 + 77.3, 4) - 0.5;
    var edge = 0.84 + wob * 0.40;
    var m = 1 - N.smoothstep(edge - 0.20, edge + 0.20, d);
    var px = (ox + 330) / 170, pz = (oz + 40) / 220;
    var dp = Math.hypot(px, pz);
    var ep = 0.68 + (N.fbm(ox * 0.002 + 5.1, oz * 0.002 + 8.9, 3) - 0.5) * 0.44;
    m = Math.max(m, (1 - N.smoothstep(ep - 0.22, ep + 0.22, dp)) * 0.9);
    return m;
  }

  // 椭圆掩膜（wobble 噪声扰动海岸）
  function ellipseMask(x, z, cx, cz, rx, rz, wFreq, wAmp, seed) {
    var ex = (x - cx) / rx, ez = (z - cz) / rz;
    var d = Math.hypot(ex, ez);
    var wob = N.fbm(x * wFreq + seed, z * wFreq + seed * 1.7, 3) - 0.5;
    var edge = 0.92 + wob * wAmp;
    return 1 - N.smoothstep(edge - 0.22, edge + 0.22, d);
  }

  // 碎浪群岛（六岛，位于两大陆之间的航道上）
  var ISLES = [
    { x: 390, z: 250, rx: 55, rz: 45 },
    { x: 452, z: 302, rx: 36, rz: 30 },
    { x: 330, z: 312, rx: 30, rz: 26 },
    { x: 470, z: 218, rx: 24, rz: 20 },
    { x: 348, z: 196, rx: 18, rz: 15 },
    { x: 430, z: 342, rx: 16, rz: 14 }
  ];
  // 零散礁岛
  var SMALL_ISLES = [
    { x: 140, z: 460, rx: 22, rz: 18 },
    { x: -520, z: 250, rx: 24, rz: 20 },
    { x: 640, z: 80, rx: 20, rz: 16 },
    { x: 250, z: -430, rx: 22, rz: 18 }
  ];

  function islesMask(x, z) {
    var m = 0;
    for (var i = 0; i < ISLES.length; i++) {
      var L = ISLES[i];
      var d = Math.hypot((x - L.x) / L.rx, (z - L.z) / L.rz);
      var wob = N.fbm(x * 0.008 + i * 7.1, z * 0.008 + i * 3.3, 2) - 0.5;
      var e = 0.85 + wob * 0.3;
      m = Math.max(m, 1 - N.smoothstep(e - 0.2, e + 0.2, d));
    }
    for (var j = 0; j < SMALL_ISLES.length; j++) {
      var S = SMALL_ISLES[j];
      var d2 = Math.hypot((x - S.x) / S.rx, (z - S.z) / S.rz);
      m = Math.max(m, 1 - N.smoothstep(0.6, 1.0, d2));
    }
    return m;
  }

  // 各大陆掩膜分量
  function maskParts(x, z) {
    var o = toOld(x, z);
    var mMain = mainMask(o.x, o.z);
    // 暮影大陆（北）：主块 + 南部半岛
    var mMist = Math.max(
      ellipseMask(x, z, 40, 620, 360, 240, 0.0016, 0.42, 51.7),
      ellipseMask(x, z, -190, 480, 130, 100, 0.0022, 0.36, 83.3) * 0.92
    );
    // 铜脊大陆（东）：主块 + 西北半岛
    var mCopper = Math.max(
      ellipseMask(x, z, 560, -160, 330, 350, 0.0016, 0.42, 29.9),
      ellipseMask(x, z, 370, -380, 100, 80, 0.0024, 0.34, 67.1) * 0.9
    );
    var mIsles = islesMask(x, z);
    return { mMain: mMain, mMist: mMist, mCopper: mCopper, mIsles: mIsles,
      m: Math.max(Math.max(mMain, mMist), Math.max(mCopper, mIsles)) };
  }

  function continentMask(x, z) {
    return maskParts(x, z).m;
  }

  /* ---------------- 基础地形 ---------------- */

  // 主大陆高度（旧 v2 设计，输入旧坐标）
  function mainH(ox, oz) {
    var base = (N.fbm(ox * 0.0021 + 3.7, oz * 0.0021 + 9.1, 5) - 0.44) * 20;
    var md = Math.hypot((ox + 110) / 270, (oz + 265) / 215);
    var mtn = 1 - N.smoothstep(0.55, 1.05, md);
    var ridge = N.ridged(ox * 0.0038 + 1.3, oz * 0.0038 + 5.7, 5);
    var mtnH = Math.pow(ridge, 2.1) * 68 * mtn;
    var sd = Math.hypot((ox + 300) / 240, (oz - 40) / 260);
    var steppe = (1 - N.smoothstep(0.4, 1.0, sd)) * 8;
    var pd = Math.hypot((ox - 180) / 190, (oz - 120) / 160);
    var plateau = (1 - N.smoothstep(0.5, 1.05, pd)) * 5;
    var hd = Math.hypot((ox - 60) / 230, (oz - 260) / 200);
    var hills = (1 - N.smoothstep(0.5, 1.0, hd)) * 5;
    var cd = Math.hypot((ox + 10) / 200, (oz - 30) / 180);
    var plains = (1 - N.smoothstep(0.55, 1.1, cd)) * 4;
    var small = (N.fbm(ox * 0.006 + 7.7, oz * 0.006 + 2.2, 3) - 0.5) * 7;
    return base + mtnH + steppe + plateau + hills + plains + small;
  }

  // 暮影大陆高度：死寂高原 + 北方亡者山脉 + 西南断崖台地 + 中央低洼（影湖）
  function mistH(x, z) {
    var base = (N.fbm(x * 0.0023 + 41.2, z * 0.0023 + 17.9, 5) - 0.46) * 24;
    var nd = Math.hypot((x - 20) / 260, (z - 780) / 150);
    var ridge = N.ridged(x * 0.004 + 71.3, z * 0.004 + 3.1, 5);
    var range = (1 - N.smoothstep(0.5, 1.05, nd)) * Math.pow(ridge, 2.0) * 48;
    var md = Math.hypot((x - 50) / 230, (z - 600) / 160);
    var mesa = (1 - N.smoothstep(0.5, 1.0, md)) * 13;
    var gd = Math.hypot((x + 170) / 190, (z - 520) / 150);
    var cliff = (1 - N.smoothstep(0.45, 1.0, gd)) * 9;
    var ed = Math.hypot((x - 240) / 170, (z - 700) / 140);
    var east = (1 - N.smoothstep(0.5, 1.0, ed)) * 7;
    var bd = Math.hypot((x - 50) / 170, (z - 640) / 120);
    var basin = N.smoothstep(0.7, 0.25, bd) * 6; // 中央低洼
    var small = (N.fbm(x * 0.007 + 11.4, z * 0.007 + 55.6, 3) - 0.5) * 6;
    return base + range + mesa + cliff + east - basin + small - 1.5;
  }

  // 铜脊大陆高度：中央铜脊山脉 + 西原 + 南部丘陵
  function copperH(x, z) {
    var base = (N.fbm(x * 0.0022 + 23.8, z * 0.0022 + 88.1, 5) - 0.44) * 18;
    var md = Math.hypot((x - 560) / 230, (z - -140) / 270);
    var mtn = 1 - N.smoothstep(0.5, 1.0, md);
    var ridge = N.ridged(x * 0.0036 + 12.7, z * 0.0036 + 44.2, 5);
    var mtnH = Math.pow(ridge, 2.1) * 56 * mtn;
    var wd = Math.hypot((x - 330) / 130, (z + 150) / 300);
    var plains = (1 - N.smoothstep(0.5, 1.0, wd)) * 3;
    var hd = Math.hypot((x - 560) / 160, (z - 180) / 120);
    var hills = (1 - N.smoothstep(0.5, 1.0, hd)) * 5;
    var small = (N.fbm(x * 0.006 + 33.9, z * 0.006 + 7.4, 3) - 0.5) * 6;
    return base + mtnH + plains + hills + small;
  }

  // 岛屿小丘
  function isleBumps(x, z) {
    var h = 0;
    for (var i = 0; i < ISLES.length; i++) {
      var L = ISLES[i];
      var d = Math.hypot((x - L.x) / (L.rx * 0.8), (z - L.z) / (L.rz * 0.8));
      h = Math.max(h, (1 - N.smoothstep(0.45, 1.0, d)) * (i === 0 ? 7 : 5));
    }
    for (var j = 0; j < SMALL_ISLES.length; j++) {
      var S = SMALL_ISLES[j];
      var d2 = Math.hypot((x - S.x) / (S.rx * 0.8), (z - S.z) / (S.rz * 0.8));
      h = Math.max(h, (1 - N.smoothstep(0.45, 1.0, d2)) * 4);
    }
    return h;
  }

  function rawH(x, z) {
    var P = maskParts(x, z);
    var cm = P.m;
    if (cm <= 0.002) return -34;
    var o = toOld(x, z);
    var h;
    if (P.mMain >= P.mMist && P.mMain >= P.mCopper) h = mainH(o.x, o.z);
    else if (P.mMist >= P.mCopper) h = mistH(x, z);
    else h = copperH(x, z);
    h += isleBumps(x, z) * P.mIsles;
    h = h * cm - (1 - cm) * 26;
    h = Math.max(h, N.smoothstep(0.25, 0.8, cm) * 5.2 - 1.6);
    return h;
  }

  /* ---------------- 网格工具 ---------------- */

  function gridOf(fn) {
    var g = new Float32Array(GRID * GRID);
    for (var iz = 0; iz < GRID; iz++) {
      for (var ix = 0; ix < GRID; ix++) {
        var x = -SIZE / 2 + SIZE * ix / SEG;
        var z = -SIZE / 2 + SIZE * iz / SEG;
        g[iz * GRID + ix] = fn(x, z);
      }
    }
    return g;
  }

  function sample(g, x, z) {
    var fx = (x + SIZE / 2) / SIZE * SEG;
    var fz = (z + SIZE / 2) / SIZE * SEG;
    var ix = Math.floor(fx), iz = Math.floor(fz);
    if (ix < 0 || ix >= SEG || iz < 0 || iz >= SEG) return -40;
    var tx = fx - ix, tz = fz - iz;
    var a = g[iz * GRID + ix], b = g[iz * GRID + ix + 1];
    var c = g[(iz + 1) * GRID + ix], d = g[(iz + 1) * GRID + ix + 1];
    return a + (b - a) * tx + (c - a) * tz + (a - b - c + d) * tx * tz;
  }

  function smoothGrid(g) {
    var out = new Float32Array(GRID * GRID);
    for (var iz = 0; iz < GRID; iz++) {
      for (var ix = 0; ix < GRID; ix++) {
        var s = 0, n = 0;
        for (var dz = -1; dz <= 1; dz++) {
          for (var dx = -1; dx <= 1; dx++) {
            var jx = ix + dx, jz = iz + dz;
            if (jx < 0 || jx >= GRID || jz < 0 || jz >= GRID) continue;
            s += g[jz * GRID + jx]; n++;
          }
        }
        out[iz * GRID + ix] = s / n;
      }
    }
    return out;
  }

  /* ---------------- 河流 ---------------- */

  function traceRiver(flow, sx, sz) {
    var path = [{ x: sx, z: sz }];
    var x = sx, z = sz, h = sample(flow, x, z);
    var dirA = Math.PI / 2;
    for (var i = 0; i < 900; i++) {
      if (h <= 0.4 && continentMask(x, z) < 0.55) break;
      var best = null, bestScore = -1e9;
      for (var k = 0; k < 8; k++) {
        var a = dirA + (k - 3.5) * 0.62;
        var nx = x + Math.cos(a) * 5, nz = z + Math.sin(a) * 5;
        var nh = sample(flow, nx, nz);
        if (nh >= h + 0.15) continue;
        var turn = Math.abs(a - dirA);
        var score = -nh - turn * 0.30;
        if (score > bestScore) { bestScore = score; best = { x: nx, z: nz, h: nh, a: a }; }
      }
      if (!best) {
        for (var f2 = 0; f2 < 60 && h > 0.4; f2++) {
          x += Math.cos(dirA) * 5; z += Math.sin(dirA) * 5;
          h = sample(flow, x, z);
          path.push({ x: x, z: z });
        }
        break;
      }
      x = best.x; z = best.z; h = best.h; dirA = best.a;
      path.push({ x: x, z: z });
    }
    return path;
  }

  function carvePath(g, mask, path) {
    var n = path.length;
    for (var i = 0; i < n; i++) {
      var t = n > 1 ? i / (n - 1) : 0;
      var width = 1.2 + t * 6.0;
      var depth = 1.8 + t * 2.8;
      var p = path[i];
      var R = Math.ceil(width * 2.4);
      var cx = (p.x + SIZE / 2) / SIZE * SEG;
      var cz = (p.z + SIZE / 2) / SIZE * SEG;
      for (var iz = -R; iz <= R; iz++) {
        for (var ix = -R; ix <= R; ix++) {
          var gx = Math.round(cx) + ix, gz = Math.round(cz) + iz;
          if (gx < 0 || gx >= GRID || gz < 0 || gz >= GRID) continue;
          var d = Math.hypot(ix, iz) * (SIZE / SEG);
          if (d > width * 2.4) continue;
          var f = Math.exp(-(d / width) * (d / width) * 1.1);
          var idx = gz * GRID + gx;
          g[idx] = g[idx] + (-depth - g[idx]) * f;
          if (f > mask[idx]) mask[idx] = f;
        }
      }
    }
  }

  function corridorPath(points, seed) {
    var path = [];
    for (var s = 0; s < points.length - 1; s++) {
      var a = points[s], b = points[s + 1];
      var ax = a[0], az = a[1], bx = b[0], bz = b[1];
      var dx = bx - ax, dz = bz - az;
      var len = Math.hypot(dx, dz);
      var steps = Math.max(2, Math.ceil(len / 4));
      var nx = -dz / len, nz = dx / len;
      for (var i = (s === 0 ? 0 : 1); i <= steps; i++) {
        var t = i / steps;
        var ph = ax * 0.05 + az * 0.07 + s * 13.7 + seed;
        var amp = 3 + 5 * Math.sin(Math.PI * Math.min(1, t * 1.15));
        N.srand(((i * 131 + s * 57 + Math.floor(seed * 13)) >>> 0) || 7);
        var off = (Math.sin(t * 6.7 + ph) * 2.8 + Math.sin(t * 17.3 + ph * 2.3) * 1.4 +
          (N.rand() - 0.5) * 2.2) * (amp / 7.5);
        path.push({ x: ax + dx * t + nx * off, z: az + dz * t + nz * off });
      }
    }
    path.push({ x: points[points.length - 1][0], z: points[points.length - 1][1] });
    return path;
  }

  function carveEstuary(g, x, z) {
    var cx = (x + SIZE / 2) / SIZE * SEG;
    var cz = (z + SIZE / 2) / SIZE * SEG;
    var R = Math.ceil(18 * SEG / SIZE);
    for (var iz = -R; iz <= R; iz++) {
      for (var ix = -R; ix <= R; ix++) {
        var gx = Math.round(cx) + ix, gz = Math.round(cz) + iz;
        if (gx < 0 || gx >= GRID || gz < 0 || gz >= GRID) continue;
        var d = Math.hypot(ix, iz) * (SIZE / SEG);
        if (d > 26) continue;
        var f = 1 - N.smoothstep(0, 26, d);
        g[gz * GRID + gx] = Math.min(g[gz * GRID + gx], -0.3 + f * 0.6);
      }
    }
  }

  function carveCorridor(g, points, width, depth) {
    var orig = g.slice();
    for (var s = 0; s < points.length - 1; s++) {
      var a = points[s], b = points[s + 1];
      var ax = a[0], az = a[1], bx = b[0], bz = b[1];
      var len = Math.hypot(bx - ax, bz - az);
      var steps = Math.ceil(len / 4);
      for (var i = 0; i <= steps; i++) {
        var t = i / steps;
        var px = ax + (bx - ax) * t;
        var pz = az + (bz - az) * t;
        var cx = (px + SIZE / 2) / SIZE * SEG;
        var cz = (pz + SIZE / 2) / SIZE * SEG;
        var R = Math.ceil(width * 1.6);
        for (var iz = -R; iz <= R; iz++) {
          for (var ix = -R; ix <= R; ix++) {
            var gx = Math.round(cx) + ix, gz = Math.round(cz) + iz;
            if (gx < 0 || gx >= GRID || gz < 0 || gz >= GRID) continue;
            var d = Math.hypot(ix, iz) * (SIZE / SEG);
            var er = width * 1.6;
            if (d > er) continue;
            var q = 1 - (d / er) * (d / er);
            var f = q * q * 0.9;
            var idx = gz * GRID + gx;
            var target = orig[idx] - f * depth;
            if (g[idx] > target) g[idx] = target;
          }
        }
      }
    }
  }

  /* ---------------- 湖泊 ---------------- */

  function carveLake(g, mask, x, z, radius, depth) {
    var cx = (x + SIZE / 2) / SIZE * SEG;
    var cz = (z + SIZE / 2) / SIZE * SEG;
    var R = Math.ceil(radius * 1.6);
    for (var iz = -R; iz <= R; iz++) {
      for (var ix = -R; ix <= R; ix++) {
        var gx = Math.round(cx) + ix, gz = Math.round(cz) + iz;
        if (gx < 0 || gx >= GRID || gz < 0 || gz >= GRID) continue;
        var d = Math.hypot(ix, iz) * (SIZE / SEG);
        var idx = gz * GRID + gx;
        if (d < radius) {
          var f = 1 - N.smoothstep(radius * 0.45, radius, d);
          g[idx] = g[idx] + (-depth - g[idx]) * f;
          if (f > (mask[idx] || 0)) mask[idx] = f;
        } else if (d < radius * 1.35) {
          var g2 = 1 - N.smoothstep(radius, radius * 1.35, d);
          g[idx] = g[idx] + Math.max(0, 1.8 - g[idx]) * g2 * 0.8;
        }
      }
    }
  }

  /* ---------------- 城市选址 ---------------- */

  function findSite(g, ax, az, opt) {
    opt = opt || {};
    var minH = opt.minH !== undefined ? opt.minH : 3;
    var maxH = opt.maxH !== undefined ? opt.maxH : 14;
    var best = null, bestScore = -1e9;

    if (opt.riverbank && riverMask) {
      for (var r3 = 0; r3 <= 80; r3 += 5) {
        var n3 = r3 === 0 ? 1 : 16;
        for (var a3 = 0; a3 < n3; a3++) {
          var ang3 = a3 / n3 * Math.PI * 2 + r3 * 0.53;
          var x3 = ax + Math.cos(ang3) * r3, z3 = az + Math.sin(ang3) * r3;
          var h3 = sample(g, x3, z3);
          if (h3 < 2.0 || h3 > 6.8) continue;
          var rmx = Math.round((x3 + SIZE / 2) / SIZE * SEG);
          var rmz = Math.round((z3 + SIZE / 2) / SIZE * SEG);
          var nearRiver = false;
          for (var dz2 = -6; dz2 <= 6 && !nearRiver; dz2++) {
            for (var dx2 = -6; dx2 <= 6; dx2++) {
              var jx = rmx + dx2, jz = rmz + dz2;
              if (jx < 0 || jx >= GRID || jz < 0 || jz >= GRID) continue;
              if (riverMask[jz * GRID + jx] > 0.06) { nearRiver = true; break; }
            }
          }
          if (!nearRiver) continue;
          var land = 0;
          for (var k3 = 0; k3 < 8; k3++) {
            var ka3 = k3 / 8 * Math.PI * 2;
            if (sample(g, x3 + Math.cos(ka3) * 55, z3 + Math.sin(ka3) * 55) > 1.2) land++;
          }
          var sc = land * 24 - Math.abs(h3 - 4.2) * 9 - r3 * 0.45;
          if (sc > bestScore) { bestScore = sc; best = { x: x3, z: z3, h: h3 }; }
        }
      }
      if (best) return best;
    }

    var radii = [0, 15, 30, 45, 60, 75, 90];
    for (var ri = 0; ri < radii.length; ri++) {
      var rr = radii[ri];
      var nAng = rr === 0 ? 1 : 12;
      for (var a = 0; a < nAng; a++) {
        var ang = a / nAng * Math.PI * 2 + ri * 0.7;
        var x = ax + Math.cos(ang) * rr, z = az + Math.sin(ang) * rr;
        var h0 = sample(g, x, z);
        if (h0 < minH || h0 > maxH) continue;
        var land = 0, wet = 0, cnt = 0;
        for (var k = 0; k < 16; k++) {
          var ka = k / 16 * Math.PI * 2;
          var hh = sample(g, x + Math.cos(ka) * 55, z + Math.sin(ka) * 55);
          if (hh > 0.8) land++; else wet++;
          cnt++;
        }
        var wetFrac = wet / cnt;
        var score = (land / cnt) * 120 - Math.abs(h0 - 7.5) * 5 - rr * 0.9;
        if (opt.coast) {
          if (wetFrac < 0.08 || wetFrac > 0.5) continue;
          score = (1 - Math.abs(wetFrac - 0.3) * 2) * 100 + (4.5 - Math.abs(h0 - 3)) * 8 - rr * 0.9;
        }
        if (opt.island) {
          if (Math.hypot(x - ax, z - az) > (opt.maxR || 60)) continue;
        }
        if (score > bestScore) { bestScore = score; best = { x: x, z: z, h: h0 }; }
      }
    }
    if (!best) {
      for (var r2 = 0; r2 <= 100; r2 += 12) {
        var n2 = r2 === 0 ? 1 : 12;
        for (var a2 = 0; a2 < n2; a2++) {
          var ang2 = a2 / n2 * Math.PI * 2;
          var x2 = ax + Math.cos(ang2) * r2, z2 = az + Math.sin(ang2) * r2;
          var h2 = sample(g, x2, z2);
          if (!best || (opt.coast ? h2 < best.h : h2 > best.h)) best = { x: x2, z: z2, h: h2 };
        }
      }
    }
    if (!best) best = { x: ax, z: az, h: sample(g, ax, az) };
    return best;
  }

  /* ---------------- 构建完整世界 ---------------- */

  function buildWorld(cfg) {
    var g = gridOf(rawH);

    riverPaths = [];
    riverMask = new Float32Array(GRID * GRID);
    for (var i = 0; i < cfg.rivers.length; i++) {
      var p = cfg.rivers[i];
      if (p.corridor) carveCorridor(g, p.corridor, p.cw || 20, p.cd || 2.4);
    }
    var flow = smoothGrid(g);
    for (var i2 = 0; i2 < cfg.rivers.length; i2++) {
      var p2 = cfg.rivers[i2];
      var path;
      if (p2.corridor) {
        path = corridorPath(p2.corridor, i2 * 101.3);
        var end = p2.corridor[p2.corridor.length - 1];
        carveEstuary(g, end[0], end[1]);
      } else {
        path = traceRiver(flow, p2.x, p2.z);
      }
      carvePath(g, riverMask, path);
      riverPaths.push(path);
    }
    lakes = cfg.lakes;
    lakeMask = new Float32Array(GRID * GRID);
    for (var l = 0; l < cfg.lakes.length; l++) {
      var L = cfg.lakes[l];
      carveLake(g, lakeMask, L.x, L.z, L.r, L.depth);
    }
    citySites = [];
    for (var c = 0; c < cfg.cities.length; c++) {
      var C = cfg.cities[c];
      var site = findSite(g, C.x, C.z, C);
      var y = N.clamp(site.h, 2.2, 16);
      citySites.push({ wx: site.x, wz: site.z, y: y, id: C.id });
      C._wx = site.x; C._wz = site.z; C._y = y;
    }
    H = new Float32Array(GRID * GRID);
    for (var iz = 0; iz < GRID; iz++) {
      for (var ix = 0; ix < GRID; ix++) {
        var x = -SIZE / 2 + SIZE * ix / SEG;
        var z = -SIZE / 2 + SIZE * iz / SEG;
        var h = g[iz * GRID + ix];
        for (var cs = 0; cs < citySites.length; cs++) {
          var cs2 = citySites[cs];
          var t = 1 - N.smoothstep(12, 34, Math.hypot(x - cs2.wx, z - cs2.wz));
          if (t > 0) h += (cs2.y - h) * t;
        }
        H[iz * GRID + ix] = h;
      }
    }
    for (var rv = 0; rv < riverPaths.length; rv++) {
      carvePath(H, riverMask, riverPaths[rv]);
    }
    return {
      H: H, riverMask: riverMask, lakeMask: lakeMask,
      citySites: citySites, riverPaths: riverPaths,
      rawH: rawH, sample: sample, sampleFinal: function (x, z) { return sample(H, x, z); },
      size: SIZE, seg: SEG, grid: GRID
    };
  }

  var api = {
    configure: configure,
    continentMask: continentMask,
    maskParts: maskParts,
    toOld: toOld,
    rawH: rawH,
    gridOf: gridOf,
    sample: sample,
    smoothGrid: smoothGrid,
    traceRiver: traceRiver,
    buildWorld: buildWorld,
    isles: ISLES,
    get H() { return H; },
    get riverMask() { return riverMask; },
    get lakeMask() { return lakeMask; },
    get citySites() { return citySites; },
    get riverPaths() { return riverPaths; },
    get size() { return SIZE; },
    get seg() { return SEG; },
    get grid() { return GRID; }
  };

  global.Terrain = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : global);
