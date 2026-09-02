/* ============================================================
 * 艾瑟兰 · 3D 世界引擎
 * 程序化地形 + 种族分布 + 城市地标 + 星辉裂隙 + 日/夜氛围
 * Three.js r128（本地 vendor）
 * ============================================================ */

var World = (function () {
  'use strict';

  /* 颜色管理：渲染器以 sRGB 输出，故我们指定（十六进制/字符串）的颜色
     在构造时统一转为线性空间，避免二次伽马导致色彩粉化。
     （(r,g,b) 三参数构造视为线性值，保持原样，兼容 Three 内部用法。） */
  (function () {
    var Base = THREE.Color;
    function ColorPatched(a, b, c) {
      var col;
      if (a === undefined) col = new Base();
      else if (arguments.length === 3) col = new Base(a, b, c);
      else {
        col = new Base(a);
        col.convertSRGBToLinear();
      }
      return col;
    }
    ColorPatched.prototype = Base.prototype;
    THREE.Color = ColorPatched;
  })();

  var SIZE = 520, SEG = 220, GRID = SEG + 1;

  var canvas, renderer, scene, camera, controls;
  var sun, hemi, skyMat, waterMat, starMat, starPoints;
  var terrain, water, rift, island, riftParticles;
  var cryMat, discMesh, ring1, ring2;
  var glowTex;
  var H = null;                    // 高度网格
  var citySites = [];              // { wx, wz, y }
  var cities3D = [];               // { data, wx, wz, y, beacon }
  var crystals = [];
  var streams = [];
  var beacons = [];                // { sprite, baseScale, baseOpacity }
  var nShards = [];
  var atmo = null;
  var presetTween = null;
  var fly = null;
  var clock = new THREE.Clock();
  var tmpV = new THREE.Vector3();
  var mouse = { x: -1e4, y: -1e4, down: null };
  var hoveredCity = null;
  var W = 1, HH = 1;
  var onHoverCb = null, onPickCb = null;
  var currentPreset = 'dawn';
  var autoRotateOn = false;

  /* ---------------- 工具 ---------------- */

  function gw(gx, gy) { return { x: gx, z: -gy }; }

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function regionWeights(x, z) {
    var out = { human: 0, elf: 0, dwarf: 0, orc: 0, halfling: 0, necro: 0 };
    var sum = 0, i, r, d, w;
    for (i = 0; i < REGIONS.length; i++) {
      r = REGIONS[i];
      d = Math.hypot(x - r.gx, z - (-r.gy));
      w = 1 - Noise.smoothstep(r.r * 0.55, r.r * 1.2, d);
      out[r.id] = w;
      sum += w;
    }
    if (sum < 0.001) { out.human = 1; sum = 1; }
    for (var k in out) out[k] /= sum;
    return out;
  }

  /* ---------------- 地形高度 ---------------- */

  function baseHeight(x, z) {
    var d = Math.hypot(x, z) / (SIZE * 0.5);
    var fall = 1 - Noise.smoothstep(0.56, 1.0, d);
    var w = regionWeights(x, z);

    var n = Noise.fbm(x * 0.0042 + 3.7, z * 0.0042 + 9.1, 5);
    var h = (n - 0.44) * 30;

    // 山脉（矮人领为主，兼有零散山岭）
    var ridge = Noise.ridged(x * 0.0075 + 1.3, z * 0.0075 + 5.7, 5);
    var mMask = w.dwarf * 1.15 + Math.max(0, Noise.fbm(x * 0.006 + 40, z * 0.006 + 40, 3) - 0.60) * 2.6;
    mMask *= (0.15 + 0.85 * fall);
    // 城市周围凿出山谷
    for (var i = 0; i < citySites.length; i++) {
      var cd = Math.hypot(x - citySites[i].wx, z - citySites[i].wz);
      var ct = 1 - Noise.smoothstep(0, 46, cd);
      if (ct > 0) mMask *= (1 - ct * 0.92);
    }
    h += Math.pow(ridge, 2.2) * 62 * mMask;

    h += (Noise.fbm(x * 0.012 + 7.7, z * 0.012 + 2.2, 3) - 0.5) * 7 * fall;
    // 区域地势：荒原高原 / 暮影高地 / 谷地丘陵
    h += (w.orc * 7 + w.necro * 5 + w.halfling * 4) * fall;
    h = h * (0.3 + 0.7 * fall) - (1 - fall) * 18;
    return h;
  }

  function heightAt(x, z) {
    var h = baseHeight(x, z);
    for (var i = 0; i < citySites.length; i++) {
      var c = citySites[i];
      var t = 1 - Noise.smoothstep(10, 30, Math.hypot(x - c.wx, z - c.wz));
      if (t > 0) h += (c.y - h) * t;
    }
    return h;
  }

  // 在锚点附近搜索最佳城市地点：海拔适中、周边陆地最多、尽量靠近锚点
  function findCitySite(ax, az) {
    var best = null, bestScore = -1e9;
    var radii = [0, 12, 24, 36, 50, 65, 80];
    for (var ri = 0; ri < radii.length; ri++) {
      var rr = radii[ri];
      var nAng = rr === 0 ? 1 : 12;
      for (var a = 0; a < nAng; a++) {
        var ang = a / nAng * Math.PI * 2 + ri * 0.7;
        var x = ax + Math.cos(ang) * rr;
        var z = az + Math.sin(ang) * rr;
        var h0 = baseHeight(x, z);
        if (h0 < 3 || h0 > 13) continue;
        var land = 0, cnt = 0;
        for (var k = 0; k < 16; k++) {
          var ka = k / 16 * Math.PI * 2;
          if (baseHeight(x + Math.cos(ka) * 46, z + Math.sin(ka) * 46) > 0.8) land++;
          cnt++;
        }
        var score = (land / cnt) * 120 - Math.abs(h0 - 7.5) * 5 - rr * 0.9;
        if (score > bestScore) { bestScore = score; best = { x: x, z: z, h: h0 }; }
      }
    }
    if (!best) {
      // 回退：取锚点附近最高的干燥点
      for (var r2 = 0; r2 <= 90; r2 += 10) {
        var n2 = r2 === 0 ? 1 : 12;
        for (var a2 = 0; a2 < n2; a2++) {
          var ang2 = a2 / n2 * Math.PI * 2;
          var x2 = ax + Math.cos(ang2) * r2;
          var z2 = az + Math.sin(ang2) * r2;
          var h2 = baseHeight(x2, z2);
          if (!best || h2 > best.h) best = { x: x2, z: z2, h: h2 };
        }
      }
      if (!best) best = { x: ax, z: az, h: baseHeight(ax, az) };
    }
    return best;
  }

  function sampleH(x, z) {
    var fx = (x + SIZE / 2) / SIZE * SEG;
    var fz = (z + SIZE / 2) / SIZE * SEG;
    var ix = Math.floor(fx), iz = Math.floor(fz);
    if (ix < 0 || ix >= SEG || iz < 0 || iz >= SEG) return 0;
    var tx = fx - ix, tz = fz - iz;
    var a = H[iz * GRID + ix], b = H[iz * GRID + ix + 1];
    var c = H[(iz + 1) * GRID + ix], d = H[(iz + 1) * GRID + ix + 1];
    return a + (b - a) * tx + (c - a) * tz + (a - b - c + d) * tx * tz;
  }

  function slopeAt(x, z) {
    var e = 3;
    return Math.max(
      Math.abs(sampleH(x + e, z) - sampleH(x - e, z)),
      Math.abs(sampleH(x, z + e) - sampleH(x, z - e))
    ) / (2 * e);
  }

  /* ---------------- 材质 / 纹理 ---------------- */

  function makeGlowTexture() {
    var cv = document.createElement('canvas');
    cv.width = cv.height = 128;
    var ctx = cv.getContext('2d');
    var g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.25, 'rgba(255,255,255,0.55)');
    g.addColorStop(0.6, 'rgba(255,255,255,0.14)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 128, 128);
    return new THREE.CanvasTexture(cv);
  }

  // C(hex|'#hex') → 线性空间颜色（供直接构造材质使用）
  function C(h) { return new THREE.Color(h); }

  function stdMat(color, opts) {
    var m = { color: C(color), roughness: 0.85, metalness: 0.05 };
    if (opts) for (var k in opts) m[k] = opts[k];
    if (m.emissive !== undefined) m.emissive = C(m.emissive);
    return new THREE.MeshStandardMaterial(m);
  }

  function addMesh(g, geo, mat, x, y, z) {
    var m = new THREE.Mesh(geo, mat);
    m.position.set(x || 0, y || 0, z || 0);
    m.castShadow = true;
    g.add(m);
    return m;
  }

  function addGlow(g, colorHex, scale, opacity, x, y, z) {
    var m = new THREE.SpriteMaterial({
      map: glowTex, color: C(colorHex), transparent: true, opacity: opacity,
      blending: THREE.AdditiveBlending, depthWrite: false
    });
    var s = new THREE.Sprite(m);
    s.scale.set(scale, scale, 1);
    s.position.set(x || 0, y || 0, z || 0);
    s.renderOrder = 5;
    g.add(s);
    return s;
  }

  /* ---------------- 天空 / 水 / 星 ---------------- */

  function buildSky() {
    skyMat = new THREE.ShaderMaterial({
      side: THREE.BackSide,
      depthWrite: false,
      uniforms: {
        uZenith: { value: new THREE.Color(0x5f74c9) },
        uHorizon: { value: new THREE.Color(0xf0b183) },
        uSunDir: { value: new THREE.Vector3(1, 0.32, 0.22).normalize() },
        uSunColor: { value: new THREE.Color(0xffd9a0) }
      },
      vertexShader: [
        'varying vec3 vDir;',
        'void main(){',
        '  vDir = position;',
        '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
        '}'
      ].join('\n'),
      fragmentShader: [
        'uniform vec3 uZenith; uniform vec3 uHorizon;',
        'uniform vec3 uSunDir; uniform vec3 uSunColor;',
        'varying vec3 vDir;',
        'void main(){',
        '  vec3 d = normalize(vDir);',
        '  float h = clamp(d.y, 0.0, 1.0);',
        '  vec3 col = mix(uHorizon, uZenith, pow(h, 0.6));',
        '  float s = max(dot(d, normalize(uSunDir)), 0.0);',
        '  col += uSunColor * (pow(s, 900.0) * 1.7 + pow(s, 20.0) * 0.30 + pow(s, 4.0) * 0.12);',
        '  if (d.y < 0.0) col = mix(col, uHorizon * 0.5, clamp(-d.y * 5.0, 0.0, 1.0));',
        '  gl_FragColor = vec4(col, 1.0);',
        '}'
      ].join('\n')
    });
    var sky = new THREE.Mesh(new THREE.SphereGeometry(1700, 32, 24), skyMat);
    sky.renderOrder = -10;
    scene.add(sky);
  }

  function buildStars() {
    var n = 1400;
    var pos = new Float32Array(n * 3);
    Noise.srand(777);
    for (var i = 0; i < n; i++) {
      var u = Noise.rand() * 2 - 1;
      var th = Noise.rand() * Math.PI * 2;
      var r = Math.sqrt(1 - u * u);
      var rad = 1550;
      pos[i * 3] = Math.cos(th) * r * rad;
      pos[i * 3 + 1] = Math.max(u, 0.02) * rad;
      pos[i * 3 + 2] = Math.sin(th) * r * rad;
    }
    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    starMat = new THREE.PointsMaterial({
      color: C(0xd8e2ff), size: 2.2, sizeAttenuation: false, map: glowTex,
      transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending
    });
    starMat.fog = false;
    starPoints = new THREE.Points(geo, starMat);
    starPoints.renderOrder = -9;
    starPoints.frustumCulled = false;
    scene.add(starPoints);
  }

  function buildWater() {
    waterMat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: {
        uTime: { value: 0 },
        uDeep: { value: new THREE.Color(0x0d3d5c) },
        uShallow: { value: new THREE.Color(0x3a9dc0) },
        uSunColor: { value: new THREE.Color(0xffe3b8) },
        uNight: { value: 0.15 },
        uFogColor: { value: new THREE.Color(0xd9b491) },
        uFogNear: { value: 420 },
        uFogFar: { value: 1500 }
      },
      vertexShader: [
        'uniform float uTime;',
        'varying vec3 vWorld;',
        'void main(){',
        '  vec3 p = position;',
        '  p.y += sin(position.x * 0.06 + uTime * 1.1) * 0.4 + cos(position.z * 0.05 + uTime * 0.7) * 0.4;',
        '  vec4 wp = modelMatrix * vec4(p, 1.0);',
        '  vWorld = wp.xyz;',
        '  gl_Position = projectionMatrix * viewMatrix * wp;',
        '}'
      ].join('\n'),
      fragmentShader: [
        'uniform vec3 uDeep; uniform vec3 uShallow; uniform vec3 uSunColor;',
        'uniform float uTime; uniform float uNight;',
        'uniform vec3 uFogColor; uniform float uFogNear; uniform float uFogFar;',
        'varying vec3 vWorld;',
        'void main(){',
        '  float w1 = sin(vWorld.x * 0.16 + uTime * 1.3);',
        '  float w2 = sin((vWorld.x + vWorld.z) * 0.12 - uTime * 0.9);',
        '  float w3 = sin(vWorld.z * 0.21 + uTime * 0.7);',
        '  float w4 = sin((vWorld.x - vWorld.z) * 0.30 + uTime * 1.7);',
        '  float w = (w1 + w2 + w3) * 0.16 + w4 * 0.06 + 0.42;',
        '  vec3 col = mix(uDeep, uShallow, clamp(w, 0.0, 1.0));',
        '  float glint = smoothstep(0.86, 1.0, w) * 0.38;',
        '  col += uSunColor * glint * (1.0 - uNight * 0.5);',
        '  col = mix(col, col * 0.35, uNight);',
        '  // 大陆架以外渐变为不透明深海（隐藏地形边界）',
        '  float beyond = max(smoothstep(228.0, 262.0, abs(vWorld.x)), smoothstep(228.0, 262.0, abs(vWorld.z)));',
        '  col = mix(col, uDeep, beyond * 0.85);',
        '  float alpha = mix(0.88, 1.0, beyond);',
        '  // 距离雾',
        '  float fogFactor = smoothstep(uFogNear, uFogFar, distance(cameraPosition, vWorld));',
        '  col = mix(col, uFogColor, fogFactor);',
        '  gl_FragColor = vec4(col, alpha);',
        '}'
      ].join('\n')
    });
    // 尺寸大于天球半径，保证海平面延伸到天际线
    var geo = new THREE.PlaneGeometry(SIZE * 8, SIZE * 8, 96, 96);
    geo.rotateX(-Math.PI / 2);
    water = new THREE.Mesh(geo, waterMat);
    water.position.y = 0;
    scene.add(water);
  }

  /* ---------------- 地形（含种族分布着色） ---------------- */

  var PAL = {
    human:    { low: new THREE.Color(0x7f9a3f), high: new THREE.Color(0xb5a86b) },
    elf:      { low: new THREE.Color(0x1c5232), high: new THREE.Color(0x2f7d4a) },
    dwarf:    { low: new THREE.Color(0x6f6257), high: new THREE.Color(0x8b8f99) },
    orc:      { low: new THREE.Color(0x7d4e33), high: new THREE.Color(0x93603c) },
    halfling: { low: new THREE.Color(0x9dc24a), high: new THREE.Color(0xc8dd7c) },
    necro:    { low: new THREE.Color(0x241a38), high: new THREE.Color(0x453363) }
  };
  var SAND = new THREE.Color(0xdcc993);
  var SNOW = new THREE.Color(0xeef3f8);
  var ROCK = new THREE.Color(0x6b6560);
  var UNDERWATER = new THREE.Color(0x24455a);
  var _c1 = new THREE.Color(), _c2 = new THREE.Color();

  function terrainColor(x, z, h) {
    var w = regionWeights(x, z);
    var t = Noise.clamp((h + 6) / 26, 0, 1);
    var out = _c2.setRGB(0, 0, 0);
    for (var k in w) {
      if (w[k] <= 0) continue;
      _c1.copy(PAL[k].low).lerp(PAL[k].high, t);
      out.r += _c1.r * w[k];
      out.g += _c1.g * w[k];
      out.b += _c1.b * w[k];
    }
    // 陡坡 → 岩石
    var s = slopeAt(x, z);
    if (s > 0.42) out.lerp(ROCK, Math.min(1, (s - 0.42) * 2.6));
    // 水下
    if (h < 0.6) out.lerp(UNDERWATER, Noise.clamp((0.6 - h) / 20, 0, 0.8));
    // 沙滩
    if (h < 2.0) out.lerp(SAND, Noise.clamp((2.0 - h) / 2.8, 0, 1));
    // 雪
    if (h > 24) out.lerp(SNOW, Math.min(1, (h - 24) / 12));
    // 细节扰动
    var v = Noise.fbm(x * 0.05 + 21, z * 0.05 + 9, 2);
    out.multiplyScalar(0.92 + 0.16 * v);
    return out;
  }

  function buildTerrain() {
    // 高度网格
    H = new Float32Array(GRID * GRID);
    var iz, ix, x, z;
    for (iz = 0; iz < GRID; iz++) {
      for (ix = 0; ix < GRID; ix++) {
        x = -SIZE / 2 + SIZE * ix / SEG;
        z = -SIZE / 2 + SIZE * iz / SEG;
        H[iz * GRID + ix] = heightAt(x, z);
      }
    }
    // 网格
    var geo = new THREE.PlaneGeometry(SIZE, SIZE, SEG, SEG);
    geo.rotateX(-Math.PI / 2);
    var pos = geo.attributes.position;
    var colors = new Float32Array(pos.count * 3);
    for (var i = 0; i < pos.count; i++) {
      x = pos.getX(i);
      z = pos.getZ(i);
      var h = sampleH(x, z);
      pos.setY(i, h);
      var col = terrainColor(x, z, h);
      colors[i * 3] = col.r;
      colors[i * 3 + 1] = col.g;
      colors[i * 3 + 2] = col.b;
    }
    pos.needsUpdate = true;
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    var mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, metalness: 0 });
    terrain = new THREE.Mesh(geo, mat);
    terrain.receiveShadow = true;
    scene.add(terrain);
  }

  /* ---------------- 植被 ---------------- */

  function buildTrees() {
    Noise.srand(20260902);
    var density = { elf: 0.85, halfling: 0.42, human: 0.30, orc: 0.05, dwarf: 0.06, necro: 0.0 };
    var ever = [], leaf = [];
    var tries = 30000;
    for (var i = 0; i < tries && (ever.length + leaf.length) < 4200; i++) {
      var x = (Noise.rand() * 2 - 1) * SIZE * 0.52;
      var z = (Noise.rand() * 2 - 1) * SIZE * 0.52;
      var h = sampleH(x, z);
      if (h < 0.9 || h > 22) continue;
      if (slopeAt(x, z) > 0.42) continue;
      var w = regionWeights(x, z);
      var dom = null, dv = 0;
      for (var k in w) if (w[k] > dv) { dv = w[k]; dom = k; }
      if (dv < 0.45) continue;
      if (Noise.rand() > density[dom]) continue;
      var nearCity = false;
      for (var ci = 0; ci < citySites.length; ci++) {
        if (Math.hypot(x - citySites[ci].wx, z - citySites[ci].wz) < 27) { nearCity = true; break; }
      }
      if (nearCity) continue;
      var site = {
        x: x, z: z, h: h,
        s: 0.7 + Noise.rand() * 0.8,
        rot: Noise.rand() * Math.PI * 2
      };
      var kind = dom === 'elf' ? (Noise.rand() < 0.72 ? 0 : 1) : (Noise.rand() < 0.45 ? 1 : 0);
      if (kind === 0) ever.push(site); else leaf.push(site);
    }

    var trunkEverGeo = new THREE.CylinderGeometry(0.32, 0.55, 2.6, 5);
    trunkEverGeo.translate(0, 1.3, 0);
    var coneEverGeo = new THREE.ConeGeometry(2.1, 5.6, 7);
    coneEverGeo.translate(0, 2.4 + 2.8, 0);
    var trunkLeafGeo = new THREE.CylinderGeometry(0.28, 0.45, 2.2, 5);
    trunkLeafGeo.translate(0, 1.1, 0);
    var blobLeafGeo = new THREE.IcosahedronGeometry(2.2, 0);
    blobLeafGeo.translate(0, 3.7, 0);
    blobLeafGeo.scale(1, 0.85, 1);

    addTreeSet(ever, trunkEverGeo, coneEverGeo, stdMat(0x6b4a30), stdMat(0x1d5230));
    addTreeSet(leaf, trunkLeafGeo, blobLeafGeo, stdMat(0x7a5535), stdMat(0x4e8030));
  }

  function addTreeSet(list, trunkGeo, leafGeo, trunkMat, leafMat) {
    if (!list.length) return;
    var m1 = new THREE.InstancedMesh(trunkGeo, trunkMat, list.length);
    var m2 = new THREE.InstancedMesh(leafGeo, leafMat, list.length);
    var dummy = new THREE.Object3D();
    for (var i = 0; i < list.length; i++) {
      var s = list[i];
      dummy.position.set(s.x, s.h - 0.15, s.z);
      dummy.rotation.set(0, s.rot, 0);
      dummy.scale.set(s.s, s.s, s.s);
      dummy.updateMatrix();
      m1.setMatrixAt(i, dummy.matrix);
      m2.setMatrixAt(i, dummy.matrix);
    }
    m1.castShadow = m2.castShadow = true;
    m1.instanceMatrix.needsUpdate = true;
    m2.instanceMatrix.needsUpdate = true;
    scene.add(m1, m2);
  }

  /* ---------------- 城市建筑 ---------------- */

  function buildCities() {
    var wallGeo = new THREE.BoxGeometry(1, 1, 1);
    wallGeo.translate(0, 0.5, 0);
    var roofGeo = new THREE.ConeGeometry(0.85, 0.9, 4);
    roofGeo.translate(0, 0.45, 0);
    roofGeo.rotateY(Math.PI / 4);

    var walls = [], roofs = [], wallCols = [], roofCols = [];
    Noise.srand(99123);
    var wallBase = {
      human: 0xe9dcbd, elf: 0xe2e9e4, dwarf: 0x9a8a78,
      orc: 0x5c4a42, halfling: 0xe4d5ac, necro: 0x3b3150
    };
    for (var ci = 0; ci < CITIES.length; ci++) {
      var c = CITIES[ci];
      if (c.race === 'rift') continue;
      var R = c.id === 'whitecrown' ? 25 : (c.id === 'silence' ? 11 : 18);
      var count = c.id === 'whitecrown' ? 84 : 44;
      var roofC = new THREE.Color(RACES[c.race].color);
      var placed = 0, guard = 0;
      while (placed < count && guard++ < count * 40) {
        var a = Noise.rand() * Math.PI * 2;
        var rr = Math.sqrt(Noise.rand()) * R;
        var x = c._wx + Math.cos(a) * rr;
        var z = c._wz + Math.sin(a) * rr;
        var h = sampleH(x, z);
        if (h < 1.6) continue;
        var ok = Math.hypot(x - c._wx, z - c._wz) > 6;
        if (ok) {
          for (var p = 0; p < walls.length; p++) {
            if (Math.abs(walls[p].x - x) < 3.4 && Math.abs(walls[p].z - z) < 3.4) { ok = false; break; }
          }
        }
        if (!ok) continue;
        var w = 2.0 + Noise.rand() * 2.2;
        var d = 2.0 + Noise.rand() * 2.2;
        var bh = 1.8 + Noise.rand() * 3.2 + (1 - rr / R) * 2.6;
        var rot = (Noise.rand() < 0.5 ? 0 : Math.PI / 2) + (Noise.rand() - 0.5) * 0.2;
        var dummy = new THREE.Object3D();
        dummy.position.set(x, h - 0.1, z);
        dummy.rotation.set(0, rot, 0);
        dummy.scale.set(w, bh, d);
        dummy.updateMatrix();
        walls.push({ m: dummy.matrix.clone(), x: x, z: z });
        dummy.position.set(x, h - 0.1 + bh, z);
        dummy.scale.set(w * 1.28, 0.7 + Noise.rand() * 0.5, d * 1.28);
        dummy.updateMatrix();
        roofs.push({ m: dummy.matrix.clone() });
        var wc = new THREE.Color(wallBase[c.race]).multiplyScalar(0.88 + Noise.rand() * 0.2);
        wallCols.push(wc);
        roofCols.push(roofC.clone().multiplyScalar(0.72 + Noise.rand() * 0.38));
        placed++;
      }
    }
    var wallMesh = new THREE.InstancedMesh(
      wallGeo, new THREE.MeshStandardMaterial({ roughness: 0.85, metalness: 0.05 }), walls.length
    );
    var roofMesh = new THREE.InstancedMesh(
      roofGeo, new THREE.MeshStandardMaterial({ roughness: 0.7, metalness: 0.15 }), roofs.length
    );
    for (var i = 0; i < walls.length; i++) {
      wallMesh.setMatrixAt(i, walls[i].m);
      wallMesh.setColorAt(i, wallCols[i]);
      roofMesh.setMatrixAt(i, roofs[i].m);
      roofMesh.setColorAt(i, roofCols[i]);
    }
    wallMesh.castShadow = roofMesh.castShadow = true;
    if (wallMesh.instanceColor) wallMesh.instanceColor.needsUpdate = true;
    if (roofMesh.instanceColor) roofMesh.instanceColor.needsUpdate = true;
    scene.add(wallMesh, roofMesh);
  }

  /* ---------------- 城市地标 ---------------- */

  function buildLandmarks() {
    for (var i = 0; i < CITIES.length; i++) {
      var c = CITIES[i];
      var g = new THREE.Group();
      g.position.set(c._wx, c._y, c._wz);
      var rc = RACES[c.race] || RACES.human;

      if (c.race === 'rift') {
        // 星辉圣所：白色圣殿门
        addMesh(g, new THREE.BoxGeometry(1.6, 9, 1.6), stdMat(0xf2f4f8), -5, 4.5, 6);
        addMesh(g, new THREE.BoxGeometry(1.6, 9, 1.6), stdMat(0xf2f4f8), 5, 4.5, 6);
        addMesh(g, new THREE.BoxGeometry(12, 2.2, 2.2), stdMat(0xe8ecf2), 0, 9.5, 6);
      }
      if (c.race === 'human') {
        var keep = addMesh(g, new THREE.BoxGeometry(7, 13, 7), stdMat(0xf0e8d4), 0, 6.5, 0);
        var roof = addMesh(g, new THREE.ConeGeometry(5.4, 5, 4), stdMat(0xd9b45b, { metalness: 0.4, roughness: 0.4 }), 0, 15.5, 0);
        roof.rotation.y = Math.PI / 4;
        for (var ti = 0; ti < 4; ti++) {
          var a = ti * Math.PI / 2 + Math.PI / 4;
          var px = Math.cos(a) * 6, pz = Math.sin(a) * 6;
          addMesh(g, new THREE.CylinderGeometry(1.1, 1.3, 10, 8), stdMat(0xe8ddc4), px, 5, pz);
          addMesh(g, new THREE.ConeGeometry(1.7, 2.6, 8), stdMat(0xd9b45b, { metalness: 0.4 }), px, 11.2, pz);
        }
      }
      if (c.race === 'elf') {
        // 千岁梧桐：巨树王庭
        addMesh(g, new THREE.CylinderGeometry(2.2, 3.8, 16, 8), stdMat(0x7a5a3a), 0, 8, 0);
        var crownMat = stdMat(0x1e5c38, { roughness: 1 });
        var c1 = addMesh(g, new THREE.IcosahedronGeometry(6.4, 1), crownMat, 0, 18.5, 0);
        c1.scale.set(1.25, 0.9, 1.15);
        var c2 = addMesh(g, new THREE.IcosahedronGeometry(4.8, 1), crownMat, 4.8, 15.5, 1.2);
        c2.scale.set(1.2, 0.85, 1.1);
        var c3 = addMesh(g, new THREE.IcosahedronGeometry(4.4, 1), crownMat, -4.4, 16, -1.6);
        c3.scale.set(1.15, 0.85, 1.1);
      }
      if (c.race === 'dwarf') {
        addMesh(g, new THREE.BoxGeometry(9, 6, 7), stdMat(0x8a7a68), 0, 3, 0);
        var dRoof = addMesh(g, new THREE.ConeGeometry(6.8, 4, 4), stdMat(0xb06a2c, { metalness: 0.3 }), 0, 8, 0);
        dRoof.rotation.y = Math.PI / 4;
        addMesh(g, new THREE.CylinderGeometry(0.9, 1.2, 9, 8), stdMat(0x6a5a4c), 3.5, 8.5, -2);
      }
      if (c.race === 'orc') {
        addMesh(g, new THREE.CylinderGeometry(2.6, 3.2, 3, 8), stdMat(0x4a3a34), 0, 1.5, 0);
        addMesh(g, new THREE.CylinderGeometry(1.9, 2.4, 4, 8), stdMat(0x5a4a42), 0, 5, 0);
        addMesh(g, new THREE.BoxGeometry(2.6, 3, 2.6), stdMat(0x6a4a3a), 0, 9.5, 0);
        addMesh(g, new THREE.CylinderGeometry(0.2, 0.25, 9, 6), stdMat(0x3a2f2a), -6, 4.5, 3);
        var b1 = new THREE.Mesh(new THREE.PlaneGeometry(3, 1.8), stdMat(0x7a2a1e, { side: THREE.DoubleSide }));
        b1.position.set(-4.5, 8, 3); b1.castShadow = true; g.add(b1);
        addMesh(g, new THREE.CylinderGeometry(0.2, 0.25, 9, 6), stdMat(0x3a2f2a), 6, 4.5, 3);
        var b2 = b1.clone(); b2.position.set(7.5, 8, 3); g.add(b2);
      }
      if (c.race === 'halfling') {
        var house = addMesh(g, new THREE.SphereGeometry(4.5, 16, 12), stdMat(0xd9c9a0), 0, 3.2, 0);
        house.scale.set(1.3, 0.85, 1.1);
        addMesh(g, new THREE.ConeGeometry(2, 2.4, 12), stdMat(0x7aa84a), 0, 7.4, 0);
        addMesh(g, new THREE.BoxGeometry(1.4, 2, 0.3), stdMat(0x8a6a42), 0, 1, 4.9);
      }
      if (c.race === 'necro') {
        var darkPatch = new THREE.Mesh(
          new THREE.CircleGeometry(15, 24),
          new THREE.MeshStandardMaterial({ color: C(0x171126), roughness: 1 })
        );
        darkPatch.rotation.x = -Math.PI / 2;
        darkPatch.position.y = 0.15;
        g.add(darkPatch);
        addMesh(g, new THREE.CylinderGeometry(1.6, 3.4, 26, 6), stdMat(0x2c2440), 0, 13, 0);
        var crownGem = addMesh(g, new THREE.OctahedronGeometry(1.6),
          stdMat(0xb07ae0, { emissive: 0x6a2fa0, emissiveIntensity: 2 }), 0, 27.5, 0);
        for (var sh = 0; sh < 4; sh++) {
          var sa = sh * Math.PI / 2 + 0.5;
          addMesh(g, new THREE.OctahedronGeometry(0.8),
            stdMat(0x9a5fd8, { emissive: 0x5a2fa0, emissiveIntensity: 1.6 }),
            Math.cos(sa) * 6, 1, Math.sin(sa) * 6);
        }
      }

      // 旗帜与信标（除圣所外）
      if (c.race !== 'rift') {
        addMesh(g, new THREE.CylinderGeometry(0.18, 0.22, 11, 6), stdMat(0x8a8a92), 8.5, 5.5, 4);
        var flag = new THREE.Mesh(
          new THREE.PlaneGeometry(4.4, 2.6),
          stdMat(rc.color, { side: THREE.DoubleSide, emissive: rc.color, emissiveIntensity: 0.3 })
        );
        flag.position.set(10.8, 9.6, 4);
        flag.castShadow = true;
        g.add(flag);
        var beacon = addGlow(g, rc.color, 16, 0.55, 8.5, 11.5, 4);
        c._beacon = beacon;
        beacons.push({ sprite: beacon, baseScale: 16, baseOpacity: 0.55, color: rc.color });
      }
      scene.add(g);
    }
  }

  /* ---------------- 暮影晶簇 ---------------- */

  function buildNecroShards() {
    var rc = REGIONS[5]; // necro
    var cx = rc.gx, cz = -rc.gy;
    Noise.srand(4242);
    var mat = stdMat(0x9a5fd8, { emissive: 0x5a2fa0, emissiveIntensity: 1.4, roughness: 0.3 });
    for (var i = 0; i < 26; i++) {
      var a = Noise.rand() * Math.PI * 2;
      var rr = 18 + Noise.rand() * 95;
      var x = cx + Math.cos(a) * rr, z = cz + Math.sin(a) * rr;
      var h = sampleH(x, z);
      if (h < 0.8) continue;
      var m = new THREE.Mesh(new THREE.OctahedronGeometry(0.5 + Noise.rand() * 0.7, 0), mat);
      m.scale.set(1, 1.6 + Noise.rand(), 1);
      m.position.set(x, h + 0.6, z);
      m.rotation.y = Noise.rand() * Math.PI;
      scene.add(m);
      nShards.push(m);
    }
    for (var g = 0; g < 6; g++) {
      var a2 = Noise.rand() * Math.PI * 2;
      var r2 = 20 + Noise.rand() * 80;
      var x2 = cx + Math.cos(a2) * r2, z2 = cz + Math.sin(a2) * r2;
      var h2 = sampleH(x2, z2);
      if (h2 < 0.8) continue;
      var sp = addGlow(scene, 0x8a4fd0, 9, 0.4, x2, h2 + 2, z2);
      beacons.push({ sprite: sp, baseScale: 9, baseOpacity: 0.4, color: '#8a4fd0', shard: true });
    }
  }

  /* ---------------- 星辉裂隙 ---------------- */

  function buildRift() {
    var p = gw(RIFT_POS[0], RIFT_POS[1]);
    var y0 = sampleH(p.x, p.z);
    var g = new THREE.Group();
    g.position.set(p.x, y0, p.z);

    discMesh = new THREE.Mesh(
      new THREE.CircleGeometry(11, 40),
      new THREE.MeshBasicMaterial({
        color: C(0x7fe8ff), transparent: true, opacity: 0.3,
        blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
      })
    );
    discMesh.rotation.x = -Math.PI / 2;
    discMesh.position.y = 0.5;
    g.add(discMesh);

    cryMat = stdMat(0xbfefff, { emissive: 0x54d4f4, emissiveIntensity: 1.4, roughness: 0.2, metalness: 0.1 });
    Noise.srand(31337);
    for (var i = 0; i < 8; i++) {
      var a = i / 8 * Math.PI * 2 + Noise.rand() * 0.6;
      var rr = 4 + Noise.rand() * 5;
      var cr = new THREE.Mesh(new THREE.OctahedronGeometry(1.4 + Noise.rand() * 1.4, 0), cryMat);
      cr.scale.set(1, 1.8 + Noise.rand() * 1.6, 1);
      cr.position.set(Math.cos(a) * rr, 2 + Noise.rand() * 3, Math.sin(a) * rr);
      cr.rotation.y = Noise.rand() * Math.PI;
      cr.userData.spin = (Noise.rand() - 0.5) * 0.8;
      cr.castShadow = true;
      g.add(cr);
      crystals.push(cr);
    }

    var beam = new THREE.Mesh(
      new THREE.CylinderGeometry(2.6, 4.6, 140, 14, 1, true),
      new THREE.MeshBasicMaterial({
        color: C(0x8fe8ff), transparent: true, opacity: 0.08,
        blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
      })
    );
    beam.position.y = 70;
    g.add(beam);

    var ringMat = new THREE.MeshBasicMaterial({
      color: C(0x9feaff), transparent: true, opacity: 0.5,
      blending: THREE.AdditiveBlending, depthWrite: false
    });
    ring1 = new THREE.Mesh(new THREE.TorusGeometry(15, 0.5, 8, 72), ringMat);
    ring1.rotation.x = Math.PI / 2;
    ring1.position.y = 16;
    g.add(ring1);
    ring2 = new THREE.Mesh(new THREE.TorusGeometry(10.5, 0.35, 8, 60), ringMat);
    ring2.rotation.x = Math.PI / 2;
    ring2.position.y = 26;
    g.add(ring2);

    // 浮空岛
    island = new THREE.Group();
    var rockMat = stdMat(0x6f6660, { roughness: 1 });
    var top = addMesh(island, new THREE.CylinderGeometry(9, 7.5, 2.5, 10), rockMat, 0, 0, 0);
    var bottom = addMesh(island, new THREE.ConeGeometry(7.5, 11, 8), rockMat, 0, -6.7, 0);
    bottom.rotation.x = Math.PI;
    var soilMat = stdMat(0x4a6a35, { roughness: 1 });
    var soil = new THREE.Mesh(new THREE.CylinderGeometry(8.2, 8.2, 0.6, 10), soilMat);
    soil.position.y = 1.2;
    island.add(soil);
    for (var tt = 0; tt < 4; tt++) {
      var ta = tt * 1.7 + 0.5;
      var tr = 3.5 + (tt % 2) * 2.5;
      var trunk = addMesh(island, new THREE.CylinderGeometry(0.3, 0.5, 2.2, 5), stdMat(0x6b4a30), Math.cos(ta) * tr, 2.4, Math.sin(ta) * tr);
      var crown = addMesh(island, new THREE.ConeGeometry(1.6, 3.6, 7), stdMat(0x245c34), Math.cos(ta) * tr, 5.4, Math.sin(ta) * tr);
    }
    var icr = new THREE.Mesh(new THREE.OctahedronGeometry(1.2), cryMat);
    icr.position.set(0, 3, 0);
    icr.scale.set(1, 1.8, 1);
    island.add(icr);
    island.add(addGlow(island, 0x7fe8ff, 14, 0.5, 0, -2, 0));
    island.position.set(0, 46, 0);
    g.add(island);

    // 上升粒子
    var pn = 320;
    var pgeo = new THREE.BufferGeometry();
    var ppos = new Float32Array(pn * 3);
    Noise.srand(555);
    for (var pi = 0; pi < pn; pi++) {
      var pa = Noise.rand() * Math.PI * 2;
      var pr = Math.sqrt(Noise.rand()) * 9;
      ppos[pi * 3] = Math.cos(pa) * pr;
      ppos[pi * 3 + 1] = Noise.rand() * 42;
      ppos[pi * 3 + 2] = Math.sin(pa) * pr;
    }
    pgeo.setAttribute('position', new THREE.BufferAttribute(ppos, 3));
    var pmat = new THREE.PointsMaterial({
      color: C(0xaff4ff), size: 1.5, sizeAttenuation: true, map: glowTex,
      transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false
    });
    var pts = new THREE.Points(pgeo, pmat);
    pts.frustumCulled = false;
    g.add(pts);
    riftParticles = { geo: pgeo, n: pn, speed: 3.2 };

    scene.add(g);
    rift = g;
  }

  function updateRiftParticles(dt) {
    if (!riftParticles) return;
    var arr = riftParticles.geo.attributes.position.array;
    for (var i = 0; i < riftParticles.n; i++) {
      arr[i * 3 + 1] += riftParticles.speed * dt;
      if (arr[i * 3 + 1] > 44) arr[i * 3 + 1] = 0;
    }
    riftParticles.geo.attributes.position.needsUpdate = true;
  }

  /* ---------------- 星辉流（裂隙 → 各城） ---------------- */

  function buildStreams() {
    var p0 = gw(RIFT_POS[0], RIFT_POS[1]);
    var start = new THREE.Vector3(p0.x, sampleH(p0.x, p0.z) + 6, p0.z);
    Noise.srand(666);
    for (var i = 0; i < CITIES.length; i++) {
      var c = CITIES[i];
      if (c.race === 'rift') continue;
      var end = new THREE.Vector3(c._wx, c._y + 5, c._wz);
      var mid = start.clone().lerp(end, 0.5);
      mid.y = Math.max(start.y, end.y) + 16;
      var curve = new THREE.QuadraticBezierCurve3(start.clone(), mid, end.clone());
      var tubeMat = new THREE.MeshBasicMaterial({
        color: C(0x7fe8ff), transparent: true, opacity: 0.10,
        blending: THREE.AdditiveBlending, depthWrite: false
      });
      var tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 48, 0.5, 6, false), tubeMat);
      scene.add(tube);
      var n = 40;
      var geo = new THREE.BufferGeometry();
      var pos = new Float32Array(n * 3);
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      var ptMat = new THREE.PointsMaterial({
        color: C(0xbdf6ff), size: 1.7, map: glowTex, transparent: true, opacity: 0.85,
        blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true
      });
      var pts = new THREE.Points(geo, ptMat);
      pts.frustumCulled = false;
      scene.add(pts);
      streams.push({
        curve: curve, geo: geo, n: n, tubeMat: tubeMat, ptMat: ptMat,
        speed: 0.04 + Noise.rand() * 0.03, offset: Noise.rand()
      });
    }
  }

  function updateStreams(t) {
    var v = new THREE.Vector3();
    for (var i = 0; i < streams.length; i++) {
      var s = streams[i];
      var pos = s.geo.attributes.position.array;
      for (var j = 0; j < s.n; j++) {
        var tt = (t * s.speed + s.offset + j / s.n) % 1;
        s.curve.getPoint(tt, v);
        pos[j * 3] = v.x;
        pos[j * 3 + 1] = v.y;
        pos[j * 3 + 2] = v.z;
      }
      s.geo.attributes.position.needsUpdate = true;
    }
  }

  /* ---------------- 氛围（时间/昼夜） ---------------- */

  var PRESETS = {
    dawn: {
      zenith: 0x5f74c9, horizon: 0xf0b183, sunDir: [1.0, 0.32, 0.22], sunColor: 0xffd9a0,
      sunIntensity: 0.82, sunPos: [430, 190, 130],
      hemiSky: 0xc9b8d8, hemiGround: 0x6a5a4a, hemiIntensity: 0.52,
      fog: 0xd9b491, fogNear: 420, fogFar: 1500,
      stars: 0.18, night: 0.15,
      waterDeep: 0x0d3d5c, waterShallow: 0x3a9dc0, waterSun: 0xffe3b8
    },
    noon: {
      zenith: 0x4a8fd9, horizon: 0xcfe8f5, sunDir: [0.35, 1.0, 0.25], sunColor: 0xfff5e0,
      sunIntensity: 0.95, sunPos: [200, 480, 140],
      hemiSky: 0xdceeff, hemiGround: 0x8a7a60, hemiIntensity: 0.60,
      fog: 0xcfe3ee, fogNear: 520, fogFar: 1700,
      stars: 0, night: 0,
      waterDeep: 0x0d4a6e, waterShallow: 0x35a8d8, waterSun: 0xffffff
    },
    night: {
      zenith: 0x070b22, horizon: 0x1b2a52, sunDir: [-0.55, 0.75, -0.35], sunColor: 0x9fb4ff,
      sunIntensity: 0.34, sunPos: [-280, 380, -170],
      hemiSky: 0x2a3a66, hemiGround: 0x141420, hemiIntensity: 0.36,
      fog: 0x111832, fogNear: 380, fogFar: 1400,
      stars: 1, night: 1,
      waterDeep: 0x06182e, waterShallow: 0x14405e, waterSun: 0xbcd0ff
    }
  };

  function makeState(p) {
    return {
      zenith: new THREE.Color(p.zenith), horizon: new THREE.Color(p.horizon),
      sunDir: new THREE.Vector3(p.sunDir[0], p.sunDir[1], p.sunDir[2]).normalize(),
      sunColor: new THREE.Color(p.sunColor), sunIntensity: p.sunIntensity,
      sunPos: new THREE.Vector3(p.sunPos[0], p.sunPos[1], p.sunPos[2]),
      hemiSky: new THREE.Color(p.hemiSky), hemiGround: new THREE.Color(p.hemiGround),
      hemiIntensity: p.hemiIntensity,
      fog: new THREE.Color(p.fog), fogNear: p.fogNear, fogFar: p.fogFar,
      stars: p.stars, night: p.night,
      waterDeep: new THREE.Color(p.waterDeep), waterShallow: new THREE.Color(p.waterShallow),
      waterSun: new THREE.Color(p.waterSun)
    };
  }

  function cloneState(s) {
    return {
      zenith: s.zenith.clone(), horizon: s.horizon.clone(),
      sunDir: s.sunDir.clone(), sunColor: s.sunColor.clone(),
      sunIntensity: s.sunIntensity, sunPos: s.sunPos.clone(),
      hemiSky: s.hemiSky.clone(), hemiGround: s.hemiGround.clone(),
      hemiIntensity: s.hemiIntensity,
      fog: s.fog.clone(), fogNear: s.fogNear, fogFar: s.fogFar,
      stars: s.stars, night: s.night,
      waterDeep: s.waterDeep.clone(), waterShallow: s.waterShallow.clone(),
      waterSun: s.waterSun.clone()
    };
  }

  function lerpState(cur, from, to, k) {
    cur.zenith.copy(from.zenith).lerp(to.zenith, k);
    cur.horizon.copy(from.horizon).lerp(to.horizon, k);
    cur.sunDir.copy(from.sunDir).lerp(to.sunDir, k).normalize();
    cur.sunColor.copy(from.sunColor).lerp(to.sunColor, k);
    cur.sunIntensity = from.sunIntensity + (to.sunIntensity - from.sunIntensity) * k;
    cur.sunPos.copy(from.sunPos).lerp(to.sunPos, k);
    cur.hemiSky.copy(from.hemiSky).lerp(to.hemiSky, k);
    cur.hemiGround.copy(from.hemiGround).lerp(to.hemiGround, k);
    cur.hemiIntensity = from.hemiIntensity + (to.hemiIntensity - from.hemiIntensity) * k;
    cur.fog.copy(from.fog).lerp(to.fog, k);
    cur.fogNear = from.fogNear + (to.fogNear - from.fogNear) * k;
    cur.fogFar = from.fogFar + (to.fogFar - from.fogFar) * k;
    cur.stars = from.stars + (to.stars - from.stars) * k;
    cur.night = from.night + (to.night - from.night) * k;
    cur.waterDeep.copy(from.waterDeep).lerp(to.waterDeep, k);
    cur.waterShallow.copy(from.waterShallow).lerp(to.waterShallow, k);
    cur.waterSun.copy(from.waterSun).lerp(to.waterSun, k);
  }

  function applyAtmosphere() {
    skyMat.uniforms.uZenith.value.copy(atmo.zenith);
    skyMat.uniforms.uHorizon.value.copy(atmo.horizon);
    skyMat.uniforms.uSunDir.value.copy(atmo.sunDir);
    skyMat.uniforms.uSunColor.value.copy(atmo.sunColor);
    sun.position.copy(atmo.sunPos);
    sun.color.copy(atmo.sunColor);
    sun.intensity = atmo.sunIntensity;
    hemi.color.copy(atmo.hemiSky);
    hemi.groundColor.copy(atmo.hemiGround);
    hemi.intensity = atmo.hemiIntensity;
    scene.fog.color.copy(atmo.fog);
    scene.fog.near = atmo.fogNear;
    scene.fog.far = atmo.fogFar;
    starMat.opacity = atmo.stars;
    waterMat.uniforms.uDeep.value.copy(atmo.waterDeep);
    waterMat.uniforms.uShallow.value.copy(atmo.waterShallow);
    waterMat.uniforms.uSunColor.value.copy(atmo.waterSun);
    waterMat.uniforms.uNight.value = atmo.night;
    waterMat.uniforms.uFogColor.value.copy(atmo.fog);
    waterMat.uniforms.uFogNear.value = atmo.fogNear;
    waterMat.uniforms.uFogFar.value = atmo.fogFar;
    // 发光物随夜色增强
    var n = atmo.night;
    for (var i = 0; i < beacons.length; i++) {
      var b = beacons[i];
      var op = b.baseOpacity * (1 + n * (b.shard ? 1.4 : 0.9));
      b.sprite.material.opacity = Math.min(1, op);
      var sc = b.baseScale * (1 + n * (b.shard ? 0.35 : 0.5));
      b.sprite.scale.set(sc, sc, 1);
    }
    if (cryMat) cryMat.emissiveIntensity = 0.9 + n * 1.6;
    if (discMesh) discMesh.material.opacity = 0.22 + n * 0.22;
    for (var s2 = 0; s2 < streams.length; s2++) {
      if (streams[s2].tubeMat) streams[s2].tubeMat.opacity = 0.08 + n * 0.14;
      if (streams[s2].ptMat) streams[s2].ptMat.opacity = 0.55 + n * 0.4;
    }
  }

  /* ---------------- 交互 ---------------- */

  function updateHover() {
    var best = null, bestD = 26;
    for (var i = 0; i < cities3D.length; i++) {
      var c = cities3D[i];
      tmpV.set(c.wx, c.y + 8, c.wz).project(camera);
      if (tmpV.z > 1) continue;
      var sx = (tmpV.x * 0.5 + 0.5) * W;
      var sy = (-tmpV.y * 0.5 + 0.5) * HH;
      var d = Math.hypot(mouse.x - sx, mouse.y - sy);
      if (d < bestD) { bestD = d; best = c; }
    }
    if (best !== hoveredCity) {
      hoveredCity = best;
      canvas.style.cursor = best ? 'pointer' : 'grab';
      if (onHoverCb) onHoverCb(best ? best.data : null);
    }
  }

  /* ---------------- 初始化 ---------------- */

  function init() {
    canvas = document.getElementById('world-canvas');
    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0xd9b491, 420, 1500);

    camera = new THREE.PerspectiveCamera(50, 1, 0.5, 4000);
    camera.position.set(360, 250, 450);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 8, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 55;
    controls.maxDistance = 780;
    controls.maxPolarAngle = 1.48;
    controls.minPolarAngle = 0.08;
    controls.autoRotateSpeed = 0.45;

    glowTex = makeGlowTexture();

    hemi = new THREE.HemisphereLight(0xc9b8d8, 0x6a5a4a, 0.65);
    scene.add(hemi);
    sun = new THREE.DirectionalLight(0xffd9a0, 1.0);
    sun.position.set(430, 190, 130);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.left = -340;
    sun.shadow.camera.right = 340;
    sun.shadow.camera.top = 340;
    sun.shadow.camera.bottom = -340;
    sun.shadow.camera.near = 20;
    sun.shadow.camera.far = 1600;
    sun.shadow.bias = -0.0005;
    scene.add(sun);
    scene.add(sun.target);

    buildSky();
    buildStars();
    buildWater();

    // 城市选址（在锚点附近寻找最佳地点）
    for (var i = 0; i < CITIES.length; i++) {
      var p = gw(CITIES[i].pos[0], CITIES[i].pos[1]);
      var site = findCitySite(p.x, p.z);
      var y = Noise.clamp(site.h, 2.5, 14);
      citySites.push({ wx: site.x, wz: site.z, y: y });
      CITIES[i]._wx = site.x;
      CITIES[i]._wz = site.z;
      CITIES[i]._y = y;
    }

    buildTerrain();
    buildTrees();
    buildCities();
    buildLandmarks();
    buildNecroShards();
    buildRift();
    buildStreams();

    for (var j = 0; j < CITIES.length; j++) {
      var cd = CITIES[j];
      cities3D.push({ data: cd, wx: cd._wx, wz: cd._wz, y: cd._y });
    }

    atmo = makeState(PRESETS.dawn);
    applyAtmosphere();

    resize();
    window.addEventListener('resize', resize);

    canvas.addEventListener('pointermove', function (e) {
      var rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    });
    canvas.addEventListener('pointerdown', function (e) {
      mouse.down = [e.clientX, e.clientY];
    });
    canvas.addEventListener('click', function (e) {
      if (!mouse.down) return;
      var dx = e.clientX - mouse.down[0], dy = e.clientY - mouse.down[1];
      if (dx * dx + dy * dy < 36 && onPickCb) {
        onPickCb(hoveredCity ? hoveredCity.data : null);
      }
      mouse.down = null;
    });

    animate();
  }

  function resize() {
    var parent = canvas ? canvas.parentElement : null;
    if (!parent) return;
    var w = parent.clientWidth, h = parent.clientHeight;
    if (w === 0 || h === 0) return;
    W = w; HH = h;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  /* ---------------- 主循环 ---------------- */

  var _sv = new THREE.Vector3();

  function animate() {
    requestAnimationFrame(animate);
    var dt = Math.min(clock.getDelta(), 0.25);
    var t = clock.elapsedTime;

    if (fly) {
      fly.t += dt / fly.dur;
      var k = fly.t >= 1 ? 1 : easeInOutCubic(fly.t);
      camera.position.lerpVectors(fly.fromPos, fly.toPos, k);
      controls.target.lerpVectors(fly.fromTgt, fly.toTgt, k);
      if (fly.t >= 1) {
        fly = null;
        if (autoRotateOn) controls.autoRotate = true;
      }
    }
    controls.update();

    if (presetTween) {
      presetTween.t += dt / presetTween.dur;
      var kk = presetTween.t >= 1 ? 1 : easeInOutCubic(presetTween.t);
      lerpState(atmo, presetTween.from, presetTween.to, kk);
      if (presetTween.t >= 1) presetTween = null;
    }
    applyAtmosphere();

    waterMat.uniforms.uTime.value = t;
    updateStreams(t);
    updateRiftParticles(dt);

    for (var i = 0; i < crystals.length; i++) {
      crystals[i].rotation.y += crystals[i].userData.spin * dt;
    }
    if (ring1) ring1.rotation.z += dt * 0.3;
    if (ring2) ring2.rotation.z -= dt * 0.45;
    if (discMesh) {
      var ps = 1 + Math.sin(t * 1.4) * 0.06;
      discMesh.scale.set(ps, ps, 1);
    }
    if (island) {
      island.position.y = 46 + Math.sin(t * 0.5) * 1.6;
      island.rotation.y = t * 0.05;
    }

    renderer.render(scene, camera);
    updateHover();
  }

  /* ---------------- 对外接口 ---------------- */

  function flyTo(targetPos, dist) {
    var tgt = new THREE.Vector3(targetPos.x, targetPos.y, targetPos.z);
    var dir = camera.position.clone().sub(controls.target);
    if (dir.lengthSq() < 0.01) dir.set(0.6, 0.5, 0.6);
    dir.normalize();
    var pos = tgt.clone().add(dir.multiplyScalar(dist));
    pos.y = Math.max(pos.y, tgt.y + dist * 0.42);
    fly = {
      fromPos: camera.position.clone(), toPos: pos,
      fromTgt: controls.target.clone(), toTgt: tgt,
      t: 0, dur: 1.6
    };
    if (controls.autoRotate) {
      controls.autoRotate = false;
      autoRotateOn = false;
      if (typeof window.__syncAutoBtn === 'function') window.__syncAutoBtn(false);
    }
  }

  return {
    init: init,
    resize: resize,
    setPreset: function (name) {
      if (!PRESETS[name]) return;
      currentPreset = name;
      presetTween = { from: cloneState(atmo), to: makeState(PRESETS[name]), t: 0, dur: 1.8 };
    },
    getPreset: function () { return currentPreset; },
    flyToCity: function (data) {
      var c = data;
      var d = c.race === 'rift' ? 200 : 130;
      flyTo(new THREE.Vector3(c._wx, c._y + 4, c._wz), d);
    },
    flyToRegion: function (region) {
      var w = gw(region.gx, region.gy);
      var y = sampleH ? sampleH(w.x, w.z) : 8;
      flyTo(new THREE.Vector3(w.x, Math.max(y, 6) + 6, w.z), 260);
    },
    resetView: function () {
      fly = {
        fromPos: camera.position.clone(),
        toPos: new THREE.Vector3(360, 250, 450),
        fromTgt: controls.target.clone(),
        toTgt: new THREE.Vector3(0, 8, 0),
        t: 0, dur: 1.6
      };
    },
    setAutoRotate: function (b) {
      autoRotateOn = b;
      controls.autoRotate = b && !fly;
    },
    getAutoRotate: function () { return autoRotateOn; },
    onHover: function (cb) { onHoverCb = cb; },
    onPick: function (cb) { onPickCb = cb; }
  };
})();
