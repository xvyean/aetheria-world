/* ============================================================
 * 艾瑟兰 · 程序化噪声
 * 确定性 value-noise + fBm + ridged（山脊）噪声，无外部依赖
 * ============================================================ */
(function (global) {
  'use strict';

  // 32 位整数哈希（Math.imul 保证正确回绕），输出 0..1 均匀分布
  function hash2(ix, iy, seed) {
    var h = Math.imul(ix, 0x27d4eb2d) ^ Math.imul(iy, 0x165667b1) ^ Math.imul(seed, 0x9e3779b1);
    h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
    h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
    h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  }

  function smooth(t) {
    return t * t * (3 - 2 * t);
  }

  // 二维 value noise，返回 0..1
  function valueNoise(x, y, seed) {
    var ix = Math.floor(x), iy = Math.floor(y);
    var fx = x - ix, fy = y - iy;
    var v00 = hash2(ix, iy, seed);
    var v10 = hash2(ix + 1, iy, seed);
    var v01 = hash2(ix, iy + 1, seed);
    var v11 = hash2(ix + 1, iy + 1, seed);
    var ux = smooth(fx), uy = smooth(fy);
    var a = v00 + (v10 - v00) * ux;
    var b = v01 + (v11 - v01) * ux;
    return a + (b - a) * uy;
  }

  // 分形叠加，返回 0..1
  function fbm(x, y, octaves, seed) {
    octaves = octaves || 5;
    seed = seed || 1;
    var amp = 1, freq = 1, sum = 0, norm = 0;
    for (var i = 0; i < octaves; i++) {
      sum += valueNoise(x * freq, y * freq, seed + i * 101) * amp;
      norm += amp;
      amp *= 0.5;
      freq *= 2.03;
    }
    return sum / norm;
  }

  // 山脊噪声，返回 0..1（峰值更锐利，适合山脉）
  function ridged(x, y, octaves, seed) {
    octaves = octaves || 5;
    seed = seed || 7;
    var amp = 0.55, freq = 1, sum = 0, norm = 0;
    for (var i = 0; i < octaves; i++) {
      var n = valueNoise(x * freq, y * freq, seed + i * 131);
      var r = 1 - Math.abs(2 * n - 1);
      r = r * r;
      sum += r * amp;
      norm += amp;
      amp *= 0.5;
      freq *= 2.11;
    }
    return sum / norm;
  }

  // 确定性伪随机（用于摆放物体，保证每次打开布局一致）
  var _state = 88675123;
  function srand(s) { _state = s >>> 0 || 1; }
  function rand() {
    _state = (Math.imul(_state, 1664525) + 1013904223) >>> 0;
    return _state / 4294967296;
  }

  function smoothstep(a, b, x) {
    var t = (x - a) / (b - a);
    t = t < 0 ? 0 : (t > 1 ? 1 : t);
    return t * t * (3 - 2 * t);
  }

  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }

  global.Noise = {
    hash2: hash2,
    valueNoise: valueNoise,
    fbm: fbm,
    ridged: ridged,
    srand: srand,
    rand: rand,
    smoothstep: smoothstep,
    clamp: clamp
  };
})(window);
