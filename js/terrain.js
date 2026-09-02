/* ============================================================
 * 艾瑟兰 · 地形系统 v2
 * 大陆掩膜（有机海岸 + 碎浪群岛）/ 山脉 / 河流水力模拟 / 湖泊
 * 浏览器（window.Terrain）与 Node（module.exports）通用
 * ============================================================ */

(function (global) {
  'use strict';

  var N = global.Noise;
  var SIZE = 1000, SEG = 320, GRID = SEG + 1;
  var H = null;            // 最终高度网格
  var riverMask = null;    // 河流影响网格
  var lakeMask = null;     // 湖泊影响网格
  var citySites = [];      // { wx, wz, y }
  var riverPaths = [];     // 河流折线（世界坐标）
  var lakes = [];          // { x, z, r }

  function configure(size, seg) {
    SIZE = size; SEG = seg; GRID = seg + 1;
  }

  /* ---------------- 大陆掩膜 ---------------- */

  // 0..1：1 = 陆地深处，0 = 深海
  function continentMask(x, z) {
    // 主大陆：扰动椭圆
    var ex = (x + 40) / 430, ez = (z + 10) / 400;
    var d = Math.hypot(ex, ez);
    var wob = N.fbm(x * 0.0016 + 31.7, z * 0.0016 + 77.3, 4) - 0.5;
    var edge = 0.84 + wob * 0.40;
    var m = 1 - N.smoothstep(edge - 0.20, edge + 0.20, d);
    // 西部向外凸出的荒原半岛
    var px = (x + 330) / 170, pz = (z + 40) / 220;
    var dp = Math.hypot(px, pz);
    var ep = 0.68 + (N.fbm(x * 0.002 + 5.1, z * 0.002 + 8.9, 3) - 0.5) * 0.44;
    m = Math.max(m, (1 - N.smoothstep(ep - 0.22, ep + 0.22, dp)) * 0.9);
    // 碎浪群岛（主岛）
    var ix = (x - 330) / 100, iz = (z - 380) / 90;
    var di = Math.hypot(ix, iz);
    var ei = 0.75 + (N.fbm(x * 0.004 + 9.3, z * 0.004 + 13.7, 3) - 0.5) * 0.44;
    m = Math.max(m, 1 - N.smoothstep(ei - 0.2, ei + 0.2, di));
    // 两枚礁岛
    var j1 = Math.hypot((x - 445) / 48, (z - 295) / 42);
    m = Math.max(m, 1 - N.smoothstep(0.55, 0.95, j1));
    var j2 = Math.hypot((x - 255) / 40, (z - 468) / 36);
    m = Math.max(m, 1 - N.smoothstep(0.55, 0.95, j2));
    return m;
  }

  /* ---------------- 基础地形 ---------------- */

  function rawH(x, z) {
    var cm = continentMask(x, z);
    if (cm <= 0.002) return -34;

    var base = (N.fbm(x * 0.0021 + 3.7, z * 0.0021 + 9.1, 5) - 0.44) * 20;

    // 铁砧山脉（北部巨龙脊背）
    var md = Math.hypot((x + 110) / 270, (z + 265) / 215);
    var mtn = 1 - N.smoothstep(0.55, 1.05, md);
    // 铜脊外山（东南）
    var bd = Math.hypot((x - 250) / 110, (z - 195) / 95);
    var mtn2 = (1 - N.smoothstep(0.5, 1.0, bd)) * 0.8;
    // 暮影暗原（最北高台）
    var nd = Math.hypot((x + 90) / 150, (z + 350) / 90);
    var mesa = (1 - N.smoothstep(0.5, 1.0, nd)) * 0.6;

    var ridge = N.ridged(x * 0.0038 + 1.3, z * 0.0038 + 5.7, 5);
    var ridge2 = N.ridged(x * 0.005 + 31.2, z * 0.005 + 71.8, 4);
    var mtnH = Math.pow(ridge, 2.1) * 68 * mtn + Math.pow(ridge2, 2.2) * 34 * mtn2;

    // 风暴荒原高原（西部）
    var sd = Math.hypot((x + 300) / 240, (z - 40) / 260);
    var steppe = (1 - N.smoothstep(0.4, 1.0, sd)) * 8;
    // 星落湖台地（中东）
    var pd = Math.hypot((x - 180) / 190, (z - 120) / 160);
    var plateau = (1 - N.smoothstep(0.5, 1.05, pd)) * 5;
    // 绿苔谷丘陵（南）
    var hd = Math.hypot((x - 60) / 230, (z - 260) / 200);
    var hills = (1 - N.smoothstep(0.5, 1.0, hd)) * 5;
    // 中央平原（略低，供城市与河流）
    var cd = Math.hypot((x + 10) / 200, (z - 30) / 180);
    var plains = (1 - N.smoothstep(0.55, 1.1, cd)) * 4;
    // 暮影高台
    var mesaH = mesa * 9;

    var small = (N.fbm(x * 0.006 + 7.7, z * 0.006 + 2.2, 3) - 0.5) * 7;

    var h = base + mtnH + steppe + plateau + hills + plains + mesaH + small;
    // 碎浪群岛小丘
    var ih = Math.hypot((x - 330) / 70, (z - 380) / 60);
    h += (1 - N.smoothstep(0.45, 1.0, ih)) * 6;
    h = h * cm - (1 - cm) * 26;
    // 内陆地板：避免内陆"内海"，保证河流通达海岸
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

  // 3x3 平滑（用于水力模拟，避免噪声坑洼卡流）
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

  /* ---------------- 河流：水力下坡追踪 + 河床雕刻 ---------------- */

  function traceRiver(flow, sx, sz) {
    var path = [{ x: sx, z: sz }];
    var x = sx, z = sz, h = sample(flow, x, z);
    var dirA = Math.PI / 2; // 初始朝南
    for (var i = 0; i < 700; i++) {
      if (h <= 0.4 && continentMask(x, z) < 0.55) break; // 抵达海岸
      var best = null, bestScore = -1e9;
      for (var k = 0; k < 8; k++) {
        var a = dirA + (k - 3.5) * 0.62;
        var nx = x + Math.cos(a) * 5, nz = z + Math.sin(a) * 5;
        var nh = sample(flow, nx, nz);
        if (nh >= h + 0.15) continue; // 只允许下坡
        var turn = Math.abs(a - dirA);
        var score = -nh - turn * 0.30;
        if (score > bestScore) { bestScore = score; best = { x: nx, z: nz, h: nh, a: a }; }
      }
      if (!best) {
        // 死路：强制沿当前方向开凿穿到海
        for (var f2 = 0; f2 < 40 && h > 0.4; f2++) {
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
      var width = 1.0 + t * 5.5;
      var depth = 1.6 + t * 2.6;
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

  // 沿折线生成蜿蜒河道（用于指定走向的河流；points 为 [x,z] 数组）
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
        var amp = 2.5 + 4.0 * Math.sin(Math.PI * Math.min(1, t * 1.15));
        N.srand(((i * 131 + s * 57 + Math.floor(seed * 13)) >>> 0) || 7);
        var off = (Math.sin(t * 7.3 + ph) * 2.4 + Math.sin(t * 19.1 + ph * 2.3) * 1.2 +
          (N.rand() - 0.5) * 2.0) * (amp / 6.5);
        path.push({ x: ax + dx * t + nx * off, z: az + dz * t + nz * off });
      }
    }
    path.push({ x: points[points.length - 1][0], z: points[points.length - 1][1] });
    return path;
  }

  // 河口：确保走廊末端挖通到海面
  function carveEstuary(g, x, z) {
    var cx = (x + SIZE / 2) / SIZE * SEG;
    var cz = (z + SIZE / 2) / SIZE * SEG;
    var R = Math.ceil(18 * SEG / SIZE);
    for (var iz = -R; iz <= R; iz++) {
      for (var ix = -R; ix <= R; ix++) {
        var gx = Math.round(cx) + ix, gz = Math.round(cz) + iz;
        if (gx < 0 || gx >= GRID || gz < 0 || gz >= GRID) continue;
        var d = Math.hypot(ix, iz) * (SIZE / SEG);
        if (d > 20) continue;
        var f = 1 - N.smoothstep(0, 20, d);
        g[gz * GRID + gx] = Math.min(g[gz * GRID + gx], -0.3 + f * 0.6);
      }
    }
  }

  // 沿折线雕刻宽缓的河道走廊（幂等：以原始高度为基准，重叠印章不叠加）
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

  /* ---------------- 湖泊雕刻 ---------------- */

  function carveLake(g, mask, x, z, radius, depth) {
    var cx = (x + SIZE / 2) / SIZE * SEG;
    var cz = (z + SIZE / 2) / SIZE * SEG;
    var R = Math.ceil(radius * 1.6);
    // 抬高边缘，确保湖面（y=0）被环抱
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
          g[idx] = g[idx] + Math.max(0, 1.8 - g[idx]) * g2 * 0.8; // 抬坝
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

    // 河畔城：紧邻河流的低处台地（如白冠城之于星辉河）
    if (opt.riverbank && riverMask) {
      for (var r3 = 0; r3 <= 70; r3 += 5) {
        var n3 = r3 === 0 ? 1 : 16;
        for (var a3 = 0; a3 < n3; a3++) {
          var ang3 = a3 / n3 * Math.PI * 2 + r3 * 0.53;
          var x3 = ax + Math.cos(ang3) * r3, z3 = az + Math.sin(ang3) * r3;
          var h3 = sample(g, x3, z3);
          if (h3 < 2.0 || h3 > 6.8) continue;
          var rmx = Math.round((x3 + SIZE / 2) / SIZE * SEG);
          var rmz = Math.round((z3 + SIZE / 2) / SIZE * SEG);
          var nearRiver = false;
          for (var dz2 = -5; dz2 <= 5 && !nearRiver; dz2++) {
            for (var dx2 = -5; dx2 <= 5; dx2++) {
              var jx = rmx + dx2, jz = rmz + dz2;
              if (jx < 0 || jx >= GRID || jz < 0 || jz >= GRID) continue;
              if (riverMask[jz * GRID + jx] > 0.06) { nearRiver = true; break; }
            }
          }
          if (!nearRiver) continue;
          var land = 0;
          for (var k3 = 0; k3 < 8; k3++) {
            var ka3 = k3 / 8 * Math.PI * 2;
            if (sample(g, x3 + Math.cos(ka3) * 50, z3 + Math.sin(ka3) * 50) > 1.2) land++;
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
          // 港口：需要水湾（水域 10%~45%），海拔更低
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
    // cfg: { cities: [{x,z,coast?,island?}], rivers: [{x,z}], lakes: [{x,z,r,depth}] }
    var g = gridOf(rawH);

    // 河流：先雕刻宽缓河道走廊引导流向，再水力追踪 + 精雕河床
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
        // 指定走向：沿走廊蜿蜒 + 河口挖通
        path = corridorPath(p2.corridor, i2 * 101.3);
        var end = p2.corridor[p2.corridor.length - 1];
        carveEstuary(g, end[0], end[1]);
      } else {
        path = traceRiver(flow, p2.x, p2.z);
      }
      carvePath(g, riverMask, path);
      riverPaths.push(path);
    }
    // 湖泊
    lakes = cfg.lakes;
    lakeMask = new Float32Array(GRID * GRID);
    for (var l = 0; l < cfg.lakes.length; l++) {
      var L = cfg.lakes[l];
      carveLake(g, lakeMask, L.x, L.z, L.r, L.depth);
    }
    // 城市
    citySites = [];
    for (var c = 0; c < cfg.cities.length; c++) {
      var C = cfg.cities[c];
      var site = findSite(g, C.x, C.z, C);
      var y = N.clamp(site.h, 2.2, 14);
      citySites.push({ wx: site.x, wz: site.z, y: y, id: C.id });
      C._wx = site.x; C._wz = site.z; C._y = y;
    }
    // 最终高度（含城市平整与凿谷）
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
    // 城市平整后重雕河床，保证河流穿城而过
    for (var rv = 0; rv < riverPaths.length; rv++) {
      carvePath(H, riverMask, riverPaths[rv]);
    }
    return {
      H: H, riverMask: riverMask, lakeMask: lakeMask,
      citySites: citySites, riverPaths: riverPaths,
      rawH: rawH, sample: sample, sampleFinal: function (x, z) { return sample(H, x, z); },
      size: SIZE, seg: SEG, grid: GRID,
      cityMask: function (x, z) {
        for (var i = 0; i < citySites.length; i++) {
          if (Math.hypot(x - citySites[i].wx, z - citySites[i].wz) < 30) return true;
        }
        return false;
      }
    };
  }

  var api = {
    configure: configure,
    continentMask: continentMask,
    rawH: rawH,
    gridOf: gridOf,
    sample: sample,
    smoothGrid: smoothGrid,
    traceRiver: traceRiver,
    buildWorld: buildWorld,
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
