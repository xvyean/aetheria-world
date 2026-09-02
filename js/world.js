/* ============================================================
 * 艾瑟兰 · 3D 世界引擎 v2
 * 大陆 + 群岛 / 三河两湖 / 十四势力 warped-Voronoi 领地
 * 村庄 / 城市地标 / 星辉裂隙 / 日·午·夜氛围
 * Three.js r128（本地 vendor）
 * ============================================================ */

var World = (function () {
  'use strict';

  /* 颜色管理：指定（十六进制/字符串）的颜色在构造时统一转为线性空间 */
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

  var SIZE, SEG, GRID;
  var canvas, renderer, scene, camera, controls;
  var sun, hemi, skyMat, waterMat, starMat, starPoints;
  var terrain, water, rift, island, riftParticles;
  var cryMat, discMesh, ring1, ring2;
  var glowTex;
  var H = null;                    // 最终高度网格
  var riverMask = null;            // 河流影响网格
  var citySites = [];              // { wx, wz, y }
  var cities3D = [];
  var villages = [];
  var crystals = [];
  var streams = [];
  var beacons = [];
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

  var START_POS = new THREE.Vector3(200, 720, 1150);
  var START_TGT = new THREE.Vector3(60, 0, 120);

  /* ---------------- 工具 ---------------- */

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  // warped-Voronoi：领地中心 + 噪声扰动距离 → top-2 权重
  function factionAt(x, z) {
    var w1 = -1, w2 = -1, i1 = -1, i2 = -1;
    for (var i = 0; i < FACTIONS.length; i++) {
      var F = FACTIONS[i];
      var d = Math.hypot(x - F.cx, z - F.cz);
      d *= 1 + 0.5 * (Noise.fbm(x * 0.004 + i * 17.31, z * 0.004 + i * 31.77, 3) - 0.5);
      if (d < 0) d = 0;
      var w = 1 - Noise.smoothstep(F.r * 0.72, F.r * 1.18, d);
      if (F.enclave) w *= 1.55;
      if (w > w1) { w2 = w1; i2 = i1; w1 = w; i1 = i; }
      else if (w > w2) { w2 = w; i2 = i; }
    }
    return { i1: i1, w1: w1, i2: i2, w2: w2 };
  }

  /* ---------------- 地形采样 ---------------- */

  function sampleH(x, z) {
    if (!H) return 0;
    var fx = (x + SIZE / 2) / SIZE * SEG;
    var fz = (z + SIZE / 2) / SIZE * SEG;
    var ix = Math.floor(fx), iz = Math.floor(fz);
    if (ix < 0 || ix >= SEG || iz < 0 || iz >= SEG) return -40;
    var tx = fx - ix, tz = fz - iz;
    var a = H[iz * GRID + ix], b = H[iz * GRID + ix + 1];
    var c = H[(iz + 1) * GRID + ix], d = H[(iz + 1) * GRID + ix + 1];
    return a + (b - a) * tx + (c - a) * tz + (a - b - c + d) * tx * tz;
  }

  function sampleRiver(x, z) {
    if (!riverMask) return 0;
    var fx = (x + SIZE / 2) / SIZE * SEG;
    var fz = (z + SIZE / 2) / SIZE * SEG;
    var ix = Math.floor(fx), iz = Math.floor(fz);
    if (ix < 0 || ix >= SEG || iz < 0 || iz >= SEG) return 0;
    var tx = fx - ix, tz = fz - iz;
    var a = riverMask[iz * GRID + ix], b = riverMask[iz * GRID + ix + 1];
    var c = riverMask[(iz + 1) * GRID + ix], d = riverMask[(iz + 1) * GRID + ix + 1];
    return a + (b - a) * tx + (c - a) * tz + (a - b - c + d) * tx * tz;
  }

  function slopeAt(x, z) {
    var e = 4;
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
    var sky = new THREE.Mesh(new THREE.SphereGeometry(5200, 32, 24), skyMat);
    sky.renderOrder = -10;
    scene.add(sky);
  }

  function buildStars() {
    var n = 3200;
    var pos = new Float32Array(n * 3);
    Noise.srand(777);
    for (var i = 0; i < n; i++) {
      var u = Noise.rand() * 2 - 1;
      var th = Noise.rand() * Math.PI * 2;
      var r = Math.sqrt(1 - u * u);
      var rad = 4900;
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
        uFogNear: { value: 700 },
        uFogFar: { value: 2800 }
      },
      vertexShader: [
        'varying vec3 vWorld;',
        'void main(){',
        '  vec4 wp = modelMatrix * vec4(position, 1.0);',
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
        '  float w1 = sin(vWorld.x * 0.11 + uTime * 1.3);',
        '  float w2 = sin((vWorld.x + vWorld.z) * 0.08 - uTime * 0.9);',
        '  float w3 = sin(vWorld.z * 0.14 + uTime * 0.7);',
        '  float w4 = sin((vWorld.x - vWorld.z) * 0.22 + uTime * 1.7);',
        '  float w5 = sin(vWorld.x * 0.031 + uTime * 0.30) * sin(vWorld.z * 0.027 - uTime * 0.22);',
        '  float w = (w1 + w2 + w3) * 0.12 + w4 * 0.05 + w5 * 0.24 + 0.42;',
        '  vec3 col = mix(uDeep, uShallow, clamp(w, 0.0, 1.0));',
        '  float glint = smoothstep(0.86, 1.0, w) * 0.38;',
        '  col += uSunColor * glint * (1.0 - uNight * 0.5);',
        '  col = mix(col, col * 0.35, uNight);',
        '  // 地形边界以外渐变为不透明深海（隐藏地形边界）',
        '  float beyond = max(smoothstep(680.0, 1150.0, abs(vWorld.x)), smoothstep(680.0, 1150.0, abs(vWorld.z)));',
        '  col = mix(col, uDeep, beyond * 0.85);',
        '  float alpha = mix(0.88, 1.0, beyond);',
        '  float fogFactor = smoothstep(uFogNear, uFogFar, distance(cameraPosition, vWorld));',
        '  col = mix(col, uFogColor, fogFactor);',
        '  gl_FragColor = vec4(col, alpha);',
        '}'
      ].join('\n')
    });
    var geo = new THREE.PlaneGeometry(SIZE * 8, SIZE * 8, 120, 120);
    geo.rotateX(-Math.PI / 2);
    water = new THREE.Mesh(geo, waterMat);
    water.position.y = 0;
    scene.add(water);
  }

  /* ---------------- 地形（势力领地着色） ---------------- */

  var PAL = {};
  var WILD = { low: new THREE.Color(0x6a7050), high: new THREE.Color(0x7a7a58) };
  var MARSH_C = new THREE.Color(0x42523a);
  var BANK_C = new THREE.Color(0x6a5f45);
  var SAND = new THREE.Color(0xdcc993);
  var SNOW = new THREE.Color(0xeef3f8);
  var ROCK = new THREE.Color(0x6b6560);
  var UNDERWATER = new THREE.Color(0x24455a);
  var _c1 = new THREE.Color(), _c2 = new THREE.Color();

  function terrainColor(x, z, h) {
    var out = _c2;
    var fw = factionAt(x, z);
    var t = Noise.clamp((h + 6) / 30, 0, 1);
    if (fw.w1 < 0.30) {
      // 荒野（无势力染指的边缘地带）
      out.copy(WILD.low).lerp(WILD.high, t);
    } else {
      var F1 = FACTIONS[fw.i1];
      var c1 = PAL[F1.id].low.clone().lerp(PAL[F1.id].high, t);
      if (fw.i2 >= 0 && fw.w2 > 0.02) {
        var F2 = FACTIONS[fw.i2];
        var c2 = PAL[F2.id].low.clone().lerp(PAL[F2.id].high, t);
        var sum = fw.w1 + fw.w2;
        c1.lerp(c2, fw.w2 / sum);
      }
      out.copy(c1);
    }
    // 雾沼：低地 + 沼泽半径
    var md = Math.hypot(x - MARSH.x, z - MARSH.z);
    if (h < 5.0 && md < MARSH.r * 1.5) {
      var mf = (1 - Noise.smoothstep(MARSH.r * 0.55, MARSH.r * 1.5, md)) *
        Noise.clamp((5.0 - h) / 5.0, 0, 1) *
        (0.7 + 0.6 * Noise.fbm(x * 0.03 + 9.1, z * 0.03 + 3.3, 2));
      out.lerp(MARSH_C, Math.min(0.75, mf));
    }
    // 河岸土色
    var rm = sampleRiver(x, z);
    if (rm > 0.04 && h > -0.5) {
      out.lerp(BANK_C, Math.min(0.5, rm * 0.9));
    }
    // 陡坡 → 岩石
    var s = slopeAt(x, z);
    if (s > 0.45) out.lerp(ROCK, Math.min(1, (s - 0.45) * 2.4));
    // 水下
    if (h < 0.6) out.lerp(UNDERWATER, Noise.clamp((0.6 - h) / 20, 0, 0.8));
    // 沙滩
    if (h < 2.0) out.lerp(SAND, Noise.clamp((2.0 - h) / 2.8, 0, 1));
    // 雪
    if (h > 36) out.lerp(SNOW, Math.min(1, (h - 36) / 14));
    // 细节扰动
    var v = Noise.fbm(x * 0.05 + 21, z * 0.05 + 9, 2);
    out.multiplyScalar(0.92 + 0.16 * v);
    return out;
  }

  function buildTerrain() {
    // 网格略低于采样分辨率（地形由 481² 采样网格双线性插值，海岸线依然平滑）
    var MS = Math.min(SEG, 340);
    var geo = new THREE.PlaneGeometry(SIZE, SIZE, MS, MS);
    geo.rotateX(-Math.PI / 2);
    var pos = geo.attributes.position;
    var colors = new Float32Array(pos.count * 3);
    var x, z, i;
    for (i = 0; i < pos.count; i++) {
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

  /* ---------------- 村庄 ---------------- */

  function buildVillages() {
    Noise.srand(424242);
    var sites = [];
    for (var fi = 0; fi < FACTIONS.length; fi++) {
      var F = FACTIONS[fi];
      var n = F.enclave ? 1 : (Noise.rand() < 0.4 ? 2 : 3);
      for (var k = 0; k < n; k++) {
        var placed = false;
        for (var attempt = 0; attempt < 40 && !placed; attempt++) {
          var a = Noise.rand() * Math.PI * 2;
          var lo = 55, hi = Math.max(lo + 20, F.r * 0.6);
          var rr = lo + Noise.rand() * (hi - lo);
          var x = F.cx + Math.cos(a) * rr, z = F.cz + Math.sin(a) * rr;
          if (Math.abs(x) > 770 || Math.abs(z) > 770) continue;
          var h = sampleH(x, z);
          if (h < 1.6 || h > 11) continue;
          if (slopeAt(x, z) > 0.4) continue;
          var ok = true;
          for (var ci = 0; ci < citySites.length; ci++) {
            if (Math.hypot(x - citySites[ci].wx, z - citySites[ci].wz) < 60) { ok = false; break; }
          }
          if (ok) for (var vi = 0; vi < sites.length; vi++) {
            if (Math.hypot(x - sites[vi].x, z - sites[vi].z) < 65) { ok = false; break; }
          }
          if (!ok) continue;
          sites.push({ x: x, z: z, h: h, F: F });
          placed = true;
        }
      }
    }
    villages = sites;
    if (!sites.length) return;

    var wallGeo = new THREE.BoxGeometry(1, 1, 1);
    wallGeo.translate(0, 0.5, 0);
    var roofGeo = new THREE.ConeGeometry(0.95, 0.9, 4);
    roofGeo.translate(0, 0.45, 0);
    roofGeo.rotateY(Math.PI / 4);
    var walls = [], roofs = [], wCols = [], rCols = [];
    for (var si = 0; si < sites.length; si++) {
      var v = sites[si];
      var nHouse = 4 + Math.floor(Noise.rand() * 5);
      var aBase = Noise.rand() * Math.PI * 2;
      for (var hh = 0; hh < nHouse; hh++) {
        var ha = aBase + hh * 2.4 + Noise.rand() * 0.8;
        var hr = 2.5 + Noise.rand() * 6;
        var hx = v.x + Math.cos(ha) * hr, hz = v.z + Math.sin(ha) * hr;
        var hht = sampleH(hx, hz);
        if (hht < 1.2) continue;
        var w = 1.5 + Noise.rand() * 1.4, d = 1.5 + Noise.rand() * 1.4;
        var bh = 1.1 + Noise.rand() * 1.3;
        var rot = ha + (Noise.rand() - 0.5) * 0.5;
        var dm = new THREE.Object3D();
        dm.position.set(hx, hht - 0.1, hz);
        dm.rotation.set(0, rot, 0);
        dm.scale.set(w, bh, d);
        dm.updateMatrix();
        walls.push(dm.matrix.clone());
        dm.position.set(hx, hht - 0.1 + bh, hz);
        dm.scale.set(w * 1.3, 0.55 + Noise.rand() * 0.3, d * 1.3);
        dm.updateMatrix();
        roofs.push(dm.matrix.clone());
        var wc = new THREE.Color(v.F.build.wall).multiplyScalar(0.85 + Noise.rand() * 0.25);
        wCols.push(wc);
        rCols.push(new THREE.Color(v.F.build.roof).multiplyScalar(0.7 + Noise.rand() * 0.4));
      }
    }
    if (!walls.length) return;
    var wallMesh = new THREE.InstancedMesh(wallGeo,
      new THREE.MeshStandardMaterial({ roughness: 0.9, metalness: 0.03 }), walls.length);
    var roofMesh = new THREE.InstancedMesh(roofGeo,
      new THREE.MeshStandardMaterial({ roughness: 0.75, metalness: 0.1 }), roofs.length);
    for (var i = 0; i < walls.length; i++) {
      wallMesh.setMatrixAt(i, walls[i]);
      wallMesh.setColorAt(i, wCols[i]);
      roofMesh.setMatrixAt(i, roofs[i]);
      roofMesh.setColorAt(i, rCols[i]);
    }
    wallMesh.castShadow = roofMesh.castShadow = true;
    scene.add(wallMesh, roofMesh);
  }

  /* ---------------- 植被 ---------------- */

  function buildTrees() {
    Noise.srand(20260902);
    var ever = [], leaf = [];
    var tries = 60000;
    for (var i = 0; i < tries && (ever.length + leaf.length) < 7000; i++) {
      var x = (Noise.rand() * 2 - 1) * SIZE * 0.49;
      var z = (Noise.rand() * 2 - 1) * SIZE * 0.49;
      var h = sampleH(x, z);
      if (h < 0.9 || h > 24) continue;
      if (slopeAt(x, z) > 0.42) continue;
      var fw = factionAt(x, z);
      if (fw.w1 < 0.35) continue;
      var F = FACTIONS[fw.i1];
      if (Noise.rand() > F.tree) continue;
      var nearCity = false;
      for (var ci = 0; ci < citySites.length; ci++) {
        if (Math.hypot(x - citySites[ci].wx, z - citySites[ci].wz) < 30) { nearCity = true; break; }
      }
      if (nearCity) continue;
      var kind;
      if (F.tree > 0.5) kind = Noise.rand() < 0.7 ? 0 : 1;
      else kind = Noise.rand() < 0.35 ? 0 : 1;
      ever.push({ x: x, z: z, h: h, s: 0.7 + Noise.rand() * 0.9, rot: Noise.rand() * Math.PI * 2, kind: kind });
    }
    // 分开收集
    var ev = [], lf = [];
    for (var j = 0; j < ever.length; j++) {
      if (ever[j].kind === 0) ev.push(ever[j]); else lf.push(ever[j]);
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

    addTreeSet(ev, trunkEverGeo, coneEverGeo, stdMat(0x6b4a30), stdMat(0x1d5230));
    addTreeSet(lf, trunkLeafGeo, blobLeafGeo, stdMat(0x7a5535), stdMat(0x4e8030));
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

  /* 每族一套屋顶形制（统一的民族风格）：
   * 人族坡顶 / 精灵尖顶 / 矮平顶石 / 兽人圆帐 / 半身人圆顶 / 暮影尖塔 / 圣地棱塔 */
  var ROOF_GEOS = {};
  function roofGeoFor(race) {
    if (ROOF_GEOS[race]) return ROOF_GEOS[race];
    var g;
    switch (race) {
      case 'elf':
        g = new THREE.ConeGeometry(0.95, 1.15, 6);
        g.translate(0, 0.575, 0);
        break;
      case 'dwarf':
        g = new THREE.BoxGeometry(1.3, 0.55, 1.3);
        g.translate(0, 0.275, 0);
        break;
      case 'orc':
        g = new THREE.ConeGeometry(1.05, 0.72, 6);
        g.translate(0, 0.36, 0);
        break;
      case 'halfling':
        g = new THREE.SphereGeometry(0.95, 10, 7, 0, Math.PI * 2, 0, Math.PI / 2);
        break;
      case 'necro':
        g = new THREE.ConeGeometry(0.72, 1.4, 4);
        g.translate(0, 0.7, 0);
        break;
      case 'rift':
        g = new THREE.ConeGeometry(0.8, 1.2, 3);
        g.translate(0, 0.6, 0);
        break;
      default: // human
        g = new THREE.ConeGeometry(0.85, 0.9, 4);
        g.translate(0, 0.45, 0);
        g.rotateY(Math.PI / 4);
    }
    ROOF_GEOS[race] = g;
    return g;
  }

  // 分层级：capital 首都 / city 大城 / town 镇 / village 村
  function buildCities() {
    var wallGeo = new THREE.BoxGeometry(1, 1, 1);
    wallGeo.translate(0, 0.5, 0);

    var TIER = {
      capital: { R: 22, count: 52, wMin: 2.0, wMax: 4.2, hMin: 1.8, hMax: 5.4, gap: 3.6 },
      city: { R: 13, count: 22, wMin: 1.6, wMax: 3.0, hMin: 1.4, hMax: 3.6, gap: 3.2 },
      town: { R: 8, count: 9, wMin: 1.2, wMax: 2.2, hMin: 1.1, hMax: 2.4, gap: 2.8 },
      village: { R: 5, count: 4, wMin: 0.9, wMax: 1.6, hMin: 0.9, hMax: 1.8, gap: 2.4 }
    };

    var walls = [];
    var roofBuckets = {}; // race -> { mats: [], cols: [] }
    Noise.srand(99123);
    for (var ci = 0; ci < CITIES.length; ci++) {
      var c = CITIES[ci];
      var F = factionOf(c);
      var T = TIER[c.tier] || TIER.village;
      if (c.id === 'whitecrown') { T.R = 30; T.count = 92; }
      if (c.id === 'silence') { T.R = 12; T.count = 30; }
      if (c.id === 'sanctum') { T.R = 13; T.count = 30; }
      var placed = 0, guard = 0;
      var maxH = c.id === 'moltenheart' ? 30 : 20;
      var minGap = T.gap;
      while (placed < T.count && guard++ < T.count * 40) {
        var a = Noise.rand() * Math.PI * 2;
        var rr = Math.sqrt(Noise.rand()) * T.R;
        var x = c._wx + Math.cos(a) * rr;
        var z = c._wz + Math.sin(a) * rr;
        var h = sampleH(x, z);
        if (h < 1.4 || h > maxH) continue;
        var ok = Math.hypot(x - c._wx, z - c._wz) > 5;
        if (ok) {
          for (var p = 0; p < walls.length; p++) {
            if (Math.abs(walls[p].x - x) < minGap && Math.abs(walls[p].z - z) < minGap) { ok = false; break; }
          }
        }
        if (!ok) continue;
        var w = T.wMin + Noise.rand() * (T.wMax - T.wMin);
        var d = T.wMin + Noise.rand() * (T.wMax - T.wMin);
        var bh = T.hMin + Noise.rand() * (T.hMax - T.hMin) + (1 - rr / T.R) * 2.4;
        var rot = (Noise.rand() < 0.5 ? 0 : Math.PI / 2) + (Noise.rand() - 0.5) * 0.2;
        var dummy = new THREE.Object3D();
        dummy.position.set(x, h - 0.1, z);
        dummy.rotation.set(0, rot, 0);
        dummy.scale.set(w, bh, d);
        dummy.updateMatrix();
        walls.push({ m: dummy.matrix.clone(), x: x, z: z, c: new THREE.Color(F.build.wall).multiplyScalar(0.88 + Noise.rand() * 0.2) });
        dummy.position.set(x, h - 0.1 + bh, z);
        dummy.scale.set(w * 1.28, 0.7 + Noise.rand() * 0.5, d * 1.28);
        dummy.updateMatrix();
        if (!roofBuckets[F.race]) roofBuckets[F.race] = { mats: [], cols: [] };
        roofBuckets[F.race].mats.push(dummy.matrix.clone());
        roofBuckets[F.race].cols.push(new THREE.Color(F.build.roof).multiplyScalar(0.72 + Noise.rand() * 0.38));
        placed++;
      }
    }
    var wallMesh = new THREE.InstancedMesh(
      wallGeo, new THREE.MeshStandardMaterial({ roughness: 0.85, metalness: 0.05 }), walls.length
    );
    for (var i = 0; i < walls.length; i++) {
      wallMesh.setMatrixAt(i, walls[i].m);
      wallMesh.setColorAt(i, walls[i].c);
    }
    wallMesh.castShadow = true;
    if (wallMesh.instanceColor) wallMesh.instanceColor.needsUpdate = true;
    scene.add(wallMesh);
    for (var race in roofBuckets) {
      var rb = roofBuckets[race];
      if (!rb.mats.length) continue;
      var roofMesh = new THREE.InstancedMesh(
        roofGeoFor(race), new THREE.MeshStandardMaterial({ roughness: 0.7, metalness: 0.15 }), rb.mats.length
      );
      for (var ri = 0; ri < rb.mats.length; ri++) {
        roofMesh.setMatrixAt(ri, rb.mats[ri]);
        roofMesh.setColorAt(ri, rb.cols[ri]);
      }
      roofMesh.castShadow = true;
      if (roofMesh.instanceColor) roofMesh.instanceColor.needsUpdate = true;
      scene.add(roofMesh);
    }
  }

  function factionOf(city) {
    for (var i = 0; i < FACTIONS.length; i++) {
      if (FACTIONS[i].id === city.faction) return FACTIONS[i];
    }
    return FACTIONS[0];
  }

  /* ---------------- 城市地标（14 城各具形态） ---------------- */

  function buildLandmarks() {
    for (var i = 0; i < CITIES.length; i++) {
      var c = CITIES[i];
      var F = factionOf(c);
      var g = new THREE.Group();
      g.position.set(c._wx, c._y, c._wz);
      var rc = F.color;

      switch (c.id) {
        case 'whitecrown': {
          var keep = addMesh(g, new THREE.BoxGeometry(7, 13, 7), stdMat(0xf0e8d4), 0, 6.5, 0);
          var roof = addMesh(g, new THREE.ConeGeometry(5.4, 5, 4), stdMat(0xd9b45b, { metalness: 0.4, roughness: 0.4 }), 0, 15.5, 0);
          roof.rotation.y = Math.PI / 4;
          for (var ti = 0; ti < 4; ti++) {
            var a = ti * Math.PI / 2 + Math.PI / 4;
            var px = Math.cos(a) * 6, pz = Math.sin(a) * 6;
            addMesh(g, new THREE.CylinderGeometry(1.1, 1.3, 10, 8), stdMat(0xe8ddc4), px, 5, pz);
            addMesh(g, new THREE.ConeGeometry(1.7, 2.6, 8), stdMat(0xd9b45b, { metalness: 0.4 }), px, 11.2, pz);
          }
          break;
        }
        case 'greyport': {
          // 灯塔
          addMesh(g, new THREE.CylinderGeometry(1.4, 2.2, 15, 10), stdMat(0xe8e2d2), 6, 7.5, 8);
          addMesh(g, new THREE.CylinderGeometry(1.9, 1.5, 2.4, 10), stdMat(0x7fa8c9, { emissive: 0x7fa8c9, emissiveIntensity: 0.5 }), 6, 16, 8);
          // 仓库
          for (var wh = 0; wh < 4; wh++) {
            var wa = wh * 1.4 + 2.2;
            addMesh(g, new THREE.BoxGeometry(5, 3.4, 4), stdMat(0xdcd4c0), Math.cos(wa) * 10, 1.7, Math.sin(wa) * 10);
          }
          // 栈桥（伸入水中）
          addMesh(g, new THREE.BoxGeometry(3.4, 0.8, 16), stdMat(0x8a7a5c), -8, 1.2, 6);
          addMesh(g, new THREE.BoxGeometry(0.8, 3.2, 0.8), stdMat(0x6a5a42), -9.5, 1.6, 12);
          addMesh(g, new THREE.BoxGeometry(0.8, 3.2, 0.8), stdMat(0x6a5a42), -6.5, 1.6, 12);
          break;
        }
        case 'dawnlight': {
          // 黄金大教堂
          addMesh(g, new THREE.BoxGeometry(9, 8, 16), stdMat(0xf2e6c4), 0, 4, 0);
          addMesh(g, new THREE.SphereGeometry(4.6, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2), stdMat(0xe8b45b, { metalness: 0.45, roughness: 0.35 }), 0, 8, -2);
          addMesh(g, new THREE.CylinderGeometry(0.5, 0.7, 4, 8), stdMat(0xd9b45b, { metalness: 0.4 }), 0, 13.6, -2);
          addMesh(g, new THREE.OctahedronGeometry(1.3), stdMat(0xffd873, { emissive: 0xd99a2b, emissiveIntensity: 1.4 }), 0, 16.4, -2);
          addMesh(g, new THREE.BoxGeometry(3, 12, 3), stdMat(0xe8dcbc), -6.5, 6, 5);
          addMesh(g, new THREE.ConeGeometry(2.3, 3.4, 8), stdMat(0xe88a3a, { metalness: 0.3 }), -6.5, 13.7, 5);
          addMesh(g, new THREE.BoxGeometry(3, 12, 3), stdMat(0xe8dcbc), 6.5, 6, 5);
          addMesh(g, new THREE.ConeGeometry(2.3, 3.4, 8), stdMat(0xe88a3a, { metalness: 0.3 }), 6.5, 13.7, 5);
          break;
        }
        case 'shatterwave': {
          // 礁岩要塞 + 风车
          addMesh(g, new THREE.BoxGeometry(6, 9, 6), stdMat(0xcfc4a8), 0, 4.5, 0);
          addMesh(g, new THREE.ConeGeometry(4.6, 3, 4), stdMat(0x4a9dc9, { metalness: 0.2 }), 0, 10.5, 0).rotation.y = Math.PI / 4;
          for (var wc2 = 0; wc2 < 4; wc2++) {
            var wa2 = wc2 * Math.PI / 2 + 0.6;
            addMesh(g, new THREE.BoxGeometry(7, 2.6, 1.2), stdMat(0xbdb298), Math.cos(wa2) * 5.5, 3, Math.sin(wa2) * 5.5).rotation.y = -wa2;
          }
          addMesh(g, new THREE.CylinderGeometry(1.6, 2.2, 7, 8), stdMat(0xe0d6bc), 8, 3.5, -6);
          addMesh(g, new THREE.ConeGeometry(2.4, 2.6, 8), stdMat(0x8a7a5c), 8, 8.3, -6);
          for (var sb = 0; sb < 4; sb++) {
            var sa3b = sb * Math.PI / 2;
            var bld = addMesh(g, new THREE.BoxGeometry(0.24, 4.6, 2.0), stdMat(0xf2ecd8), 9.2, 9, -6);
            bld.position.y += Math.cos(sa3b) * 2.3;
            bld.position.z += -Math.sin(sa3b) * 2.3;
            bld.rotation.x = sa3b;
          }
          break;
        }
        case 'silverleaf': {
          addMesh(g, new THREE.CylinderGeometry(2.2, 3.8, 16, 8), stdMat(0x7a5a3a), 0, 8, 0);
          var crownMat = stdMat(0x1e5c38, { roughness: 1 });
          var c1 = addMesh(g, new THREE.IcosahedronGeometry(6.4, 1), crownMat, 0, 18.5, 0);
          c1.scale.set(1.25, 0.9, 1.15);
          var c2 = addMesh(g, new THREE.IcosahedronGeometry(4.8, 1), crownMat, 4.8, 15.5, 1.2);
          c2.scale.set(1.2, 0.85, 1.1);
          var c3 = addMesh(g, new THREE.IcosahedronGeometry(4.4, 1), crownMat, -4.4, 16, -1.6);
          c3.scale.set(1.15, 0.85, 1.1);
          break;
        }
        case 'moonshadow': {
          // 月石环 + 垂柳
          var stoneMat = stdMat(0xbfd8d0, { emissive: 0x4fae8a, emissiveIntensity: 0.8, roughness: 0.3 });
          for (var ms = 0; ms < 12; ms++) {
            var ma = ms / 12 * Math.PI * 2;
            addMesh(g, new THREE.OctahedronGeometry(0.7, 0), stoneMat, Math.cos(ma) * 11, 0.9, Math.sin(ma) * 11)
              .scale.set(1, 1.5, 1);
          }
          addMesh(g, new THREE.CylinderGeometry(1.1, 1.9, 9, 7), stdMat(0x6a5a42), 0, 4.5, 0);
          var willow = addMesh(g, new THREE.IcosahedronGeometry(4.6, 1), stdMat(0x2f6b52, { roughness: 1 }), 0, 10.5, 0);
          willow.scale.set(1.3, 1.05, 1.3);
          break;
        }
        case 'moltenheart': {
          addMesh(g, new THREE.BoxGeometry(9, 6, 7), stdMat(0x8a7a68), 0, 3, 0);
          var dRoof = addMesh(g, new THREE.ConeGeometry(6.8, 4, 4), stdMat(0xb06a2c, { metalness: 0.3 }), 0, 8, 0);
          dRoof.rotation.y = Math.PI / 4;
          addMesh(g, new THREE.CylinderGeometry(0.9, 1.2, 9, 8), stdMat(0x6a5a4c), 3.5, 8.5, -2);
          addMesh(g, new THREE.BoxGeometry(2.6, 1.6, 2.6), stdMat(0xff8a3a, { emissive: 0xff6a1a, emissiveIntensity: 1.6 }), -3.2, 1.4, 2.4);
          addGlow(g, 0xff8a3a, 14, 0.5, -3.2, 2.6, 2.4);
          break;
        }
        case 'bronzeridge': {
          // 崖顶双塔
          addMesh(g, new THREE.CylinderGeometry(2.2, 3, 10, 8), stdMat(0x9a8468), -4, 5, 0);
          addMesh(g, new THREE.ConeGeometry(3, 3.6, 8), stdMat(0xc97a4a, { metalness: 0.35 }), -4, 11.8, 0);
          addMesh(g, new THREE.CylinderGeometry(1.9, 2.6, 8, 8), stdMat(0x9a8468), 4, 4, 2);
          addMesh(g, new THREE.ConeGeometry(2.6, 3, 8), stdMat(0xc97a4a, { metalness: 0.35 }), 4, 9.5, 2);
          addMesh(g, new THREE.BoxGeometry(9, 3.4, 1.6), stdMat(0x8a7458), 0, 4.5, 1);
          break;
        }
        case 'blackfang': {
          addMesh(g, new THREE.CylinderGeometry(2.6, 3.2, 3, 8), stdMat(0x4a3a34), 0, 1.5, 0);
          addMesh(g, new THREE.CylinderGeometry(1.9, 2.4, 4, 8), stdMat(0x5a4a42), 0, 5, 0);
          addMesh(g, new THREE.BoxGeometry(2.6, 3, 2.6), stdMat(0x6a4a3a), 0, 9.5, 0);
          addMesh(g, new THREE.CylinderGeometry(0.2, 0.25, 9, 6), stdMat(0x3a2f2a), -6, 4.5, 3);
          var b1 = new THREE.Mesh(new THREE.PlaneGeometry(3, 1.8), stdMat(0x7a2a1e, { side: THREE.DoubleSide }));
          b1.position.set(-4.5, 8, 3); b1.castShadow = true; g.add(b1);
          addMesh(g, new THREE.CylinderGeometry(0.2, 0.25, 9, 6), stdMat(0x3a2f2a), 6, 4.5, 3);
          var b2 = b1.clone(); b2.position.set(7.5, 8, 3); g.add(b2);
          break;
        }
        case 'bloodoath': {
          // 帐篷营 + 战鼓
          for (var tent = 0; tent < 5; tent++) {
            var ta = tent / 5 * Math.PI * 2 + 0.4;
            var tr = 5 + (tent % 2) * 3;
            addMesh(g, new THREE.ConeGeometry(2.2, 3, 6), stdMat(0x7a5a42), Math.cos(ta) * tr, 1.5, Math.sin(ta) * tr);
          }
          addMesh(g, new THREE.CylinderGeometry(1.6, 1.6, 2.6, 10), stdMat(0x5c3a2a), 0, 1.3, 0);
          addMesh(g, new THREE.CylinderGeometry(1.7, 1.7, 0.4, 10), stdMat(0xd8c8a8), 0, 2.8, 0);
          addMesh(g, new THREE.CylinderGeometry(0.18, 0.22, 8, 6), stdMat(0x3a2f2a), 0, 4, 0);
          var drumGem = addMesh(g, new THREE.OctahedronGeometry(0.55), stdMat(0xd05a3a, { emissive: 0xa03018, emissiveIntensity: 1.5 }), 0, 8.4, 0);
          break;
        }
        case 'goldwheat': {
          var house = addMesh(g, new THREE.SphereGeometry(4.5, 16, 12), stdMat(0xd9c9a0), 0, 3.2, 0);
          house.scale.set(1.3, 0.85, 1.1);
          addMesh(g, new THREE.ConeGeometry(2, 2.4, 12), stdMat(0x7aa84a), 0, 7.4, 0);
          addMesh(g, new THREE.BoxGeometry(1.4, 2, 0.3), stdMat(0x8a6a42), 0, 1, 4.9);
          // 粮仓
          for (var sil = 0; sil < 3; sil++) {
            var sa3 = sil * 2.1 + 1.2;
            addMesh(g, new THREE.CylinderGeometry(1.4, 1.4, 3.4, 8), stdMat(0xcfc098), Math.cos(sa3) * 8, 1.7, Math.sin(sa3) * 8);
            addMesh(g, new THREE.ConeGeometry(1.7, 1.6, 8), stdMat(0xa89050), Math.cos(sa3) * 8, 4.2, Math.sin(sa3) * 8);
          }
          break;
        }
        case 'caravan': {
          // 集市 + 钟塔 + 喷泉
          addMesh(g, new THREE.CylinderGeometry(0.9, 1.2, 12, 8), stdMat(0xe8dcb4), 0, 6, 0);
          addMesh(g, new THREE.ConeGeometry(1.9, 2.6, 8), stdMat(0xc8b84a, { metalness: 0.3 }), 0, 13.3, 0);
          addMesh(g, new THREE.SphereGeometry(0.5, 8, 8), stdMat(0xffe88a, { emissive: 0xc8a83a, emissiveIntensity: 1.2 }), 0, 15.4, 0);
          for (var stall = 0; stall < 8; stall++) {
            var sta = stall / 8 * Math.PI * 2;
            var str = 6.5;
            addMesh(g, new THREE.BoxGeometry(2.2, 1.6, 1.6), stdMat(stall % 2 ? 0xd8c8a0 : 0xcfc098), Math.cos(sta) * str, 0.8, Math.sin(sta) * str).rotation.y = -sta;
            addMesh(g, new THREE.BoxGeometry(2.6, 0.3, 2.0), stdMat(stall % 2 ? 0xc8b84a : 0x7aa84a), Math.cos(sta) * str, 1.9, Math.sin(sta) * str).rotation.y = -sta;
          }
          addMesh(g, new THREE.CylinderGeometry(1.2, 1.5, 0.9, 10), stdMat(0xb8b0a0), 3, 0.45, 5);
          break;
        }
        case 'silence': {
          var darkPatch = new THREE.Mesh(
            new THREE.CircleGeometry(15, 24),
            new THREE.MeshStandardMaterial({ color: C(0x171126), roughness: 1 })
          );
          darkPatch.rotation.x = -Math.PI / 2;
          darkPatch.position.y = 0.15;
          g.add(darkPatch);
          addMesh(g, new THREE.CylinderGeometry(1.6, 3.4, 26, 6), stdMat(0x2c2440), 0, 13, 0);
          addMesh(g, new THREE.OctahedronGeometry(1.6),
            stdMat(0xb07ae0, { emissive: 0x6a2fa0, emissiveIntensity: 2 }), 0, 27.5, 0);
          for (var sh = 0; sh < 4; sh++) {
            var sha = sh * Math.PI / 2 + 0.5;
            addMesh(g, new THREE.OctahedronGeometry(0.8),
              stdMat(0x9a5fd8, { emissive: 0x5a2fa0, emissiveIntensity: 1.6 }),
              Math.cos(sha) * 6, 1, Math.sin(sha) * 6);
          }
          break;
        }
        case 'sanctum': {
          // 白色圣殿 + 星尖
          for (var col = 0; col < 8; col++) {
            var ca = col / 8 * Math.PI * 2;
            addMesh(g, new THREE.CylinderGeometry(0.55, 0.7, 7, 8), stdMat(0xf2f4f8), Math.cos(ca) * 6, 3.5, Math.sin(ca) * 6);
          }
          addMesh(g, new THREE.BoxGeometry(11, 1.6, 11), stdMat(0xe8ecf2), 0, 7.8, 0);
          var ped = addMesh(g, new THREE.ConeGeometry(5.4, 3.4, 4), stdMat(0xf2f4f8), 0, 9.9, 0);
          ped.rotation.y = Math.PI / 4;
          addMesh(g, new THREE.CylinderGeometry(0.7, 1.1, 9, 8), stdMat(0xdfe6ee), 0, 13, 0);
          addMesh(g, new THREE.OctahedronGeometry(1.5), stdMat(0xbfefff, { emissive: 0x54d4f4, emissiveIntensity: 1.8 }), 0, 19, 0);
          break;
        }
      }

      var tier = c.tier || 'capital';
      // 大城：本族配色的小塔 + 微弱信标
      if (tier === 'city') {
        addMesh(g, new THREE.CylinderGeometry(1.0, 1.5, 7.5, 8), stdMat(F.build.wall), 6, 3.75, 5);
        addMesh(g, new THREE.ConeGeometry(1.6, 3.0, 8), stdMat(F.build.roof, { metalness: 0.3 }), 6, 9.0, 5);
        var bCity = addGlow(g, rc, 9, 0.35, 6, 11, 5);
        beacons.push({ sprite: bCity, baseScale: 9, baseOpacity: 0.35, color: rc });
      } else if (tier === 'town' || tier === 'village') {
        // 镇 / 村：一面本族色的小旗
        addMesh(g, new THREE.CylinderGeometry(0.14, 0.18, 7, 6), stdMat(0x8a8a92), 4, 3.5, 3);
        var tFlag = new THREE.Mesh(
          new THREE.PlaneGeometry(tier === 'town' ? 2.8 : 2.0, tier === 'town' ? 1.7 : 1.3),
          stdMat(rc, { side: THREE.DoubleSide, emissive: rc, emissiveIntensity: 0.3 })
        );
        tFlag.position.set(5.4, 6.2, 3);
        tFlag.castShadow = true;
        g.add(tFlag);
      }
      // 首都旗帜与信标（圣所除外）
      if (tier === 'capital' && c.id !== 'sanctum') {
        addMesh(g, new THREE.CylinderGeometry(0.18, 0.22, 11, 6), stdMat(0x8a8a92), 8.5, 5.5, 4);
        var flag = new THREE.Mesh(
          new THREE.PlaneGeometry(4.4, 2.6),
          stdMat(rc, { side: THREE.DoubleSide, emissive: rc, emissiveIntensity: 0.3 })
        );
        flag.position.set(10.8, 9.6, 4);
        flag.castShadow = true;
        g.add(flag);
        var beacon = addGlow(g, rc, 16, 0.55, 8.5, 11.5, 4);
        c._beacon = beacon;
        beacons.push({ sprite: beacon, baseScale: 16, baseOpacity: 0.55, color: rc });
      }
      scene.add(g);
    }
    buildWhiteCrownBridge();
  }

  // 白冠城的跨河石桥
  function buildWhiteCrownBridge() {
    var c = null;
    for (var i = 0; i < CITIES.length; i++) if (CITIES[i].id === 'whitecrown') c = CITIES[i];
    if (!c) return;
    var rp = null;
    for (var k = 0; k < riverPaths.length; k++) {
      if (riverPaths[k].length > 2) {
        // 找离白冠城最近的路径点
        var best = 1e9, bp = null;
        for (var j = 0; j < riverPaths[k].length; j++) {
          var d = Math.hypot(riverPaths[k][j].x - c._wx, riverPaths[k][j].z - c._wz);
          if (d < best) { best = d; bp = riverPaths[k][j]; }
        }
        if (best < 40) rp = riverPaths[k];
        if (rp) break;
      }
    }
    if (!rp) return;
    // 河流方向 → 桥垂直于河流
    var bi = 0;
    for (var m = 0; m < rp.length; m++) {
      if (Math.hypot(rp[m].x - c._wx, rp[m].z - c._wz) < Math.hypot(rp[bi].x - c._wx, rp[bi].z - c._wz)) bi = m;
    }
    var j2 = Math.min(rp.length - 1, bi + 2);
    var dx = rp[j2].x - rp[bi].x, dz = rp[j2].z - rp[bi].z;
    var ang = Math.atan2(dz, dx) + Math.PI / 2;
    var g = new THREE.Group();
    g.position.set(rp[bi].x, 0, rp[bi].z);
    g.rotation.y = -ang;
    var deckY = Math.max(c._y + 0.6, sampleH(rp[bi].x, rp[bi].z) + 3.2);
    addMesh(g, new THREE.BoxGeometry(24, 1.3, 5), stdMat(0xb8ae9a), 0, deckY, 0);
    addMesh(g, new THREE.BoxGeometry(24, 1.6, 0.7), stdMat(0xa89e8a), 0, deckY + 1.4, 2.6);
    addMesh(g, new THREE.BoxGeometry(24, 1.6, 0.7), stdMat(0xa89e8a), 0, deckY + 1.4, -2.6);
    for (var p = -2; p <= 2; p++) {
      addMesh(g, new THREE.BoxGeometry(1.6, 6, 1.6), stdMat(0x9a917f), p * 5, deckY - 2.4, 0);
    }
    scene.add(g);
  }

  /* ---------------- 暮影晶簇 ---------------- */

  function buildNecroShards() {
    var c = null;
    for (var i = 0; i < CITIES.length; i++) if (CITIES[i].id === 'silence') c = CITIES[i];
    if (!c) return;
    Noise.srand(4242);
    var mat = stdMat(0x9a5fd8, { emissive: 0x5a2fa0, emissiveIntensity: 1.4, roughness: 0.3 });
    for (var i2 = 0; i2 < 26; i2++) {
      var a = Noise.rand() * Math.PI * 2;
      var rr = 18 + Noise.rand() * 95;
      var x = c._wx + Math.cos(a) * rr, z = c._wz + Math.sin(a) * rr;
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
      var x2 = c._wx + Math.cos(a2) * r2, z2 = c._wz + Math.sin(a2) * r2;
      var h2 = sampleH(x2, z2);
      if (h2 < 0.8) continue;
      var sp = addGlow(scene, 0x8a4fd0, 9, 0.4, x2, h2 + 2, z2);
      beacons.push({ sprite: sp, baseScale: 9, baseOpacity: 0.4, color: '#8a4fd0', shard: true });
    }
  }

  /* ---------------- 星辉裂隙 ---------------- */

  var riverPaths = [];

  function buildRift() {
    var p = { x: RIFT_POS[0], z: RIFT_POS[1] };
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
      new THREE.CylinderGeometry(2.6, 4.6, 150, 14, 1, true),
      new THREE.MeshBasicMaterial({
        color: C(0x8fe8ff), transparent: true, opacity: 0.08,
        blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
      })
    );
    beam.position.y = 75;
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

  /* ---------------- 星槎学院（裂隙上空 300 丈的空岛） ---------------- */

  var academy = null;
  var academyBaseY = 0;
  var academyCrystal = null;

  function buildAcademy() {
    var p = { x: RIFT_POS[0], z: RIFT_POS[1] };
    var y0 = sampleH(p.x, p.z);
    academyBaseY = y0 + 104;
    var g = new THREE.Group();
    g.position.set(p.x, academyBaseY, p.z);

    var rockMat = stdMat(0x6f6660, { roughness: 1 });
    addMesh(g, new THREE.CylinderGeometry(30, 24, 4.5, 18), rockMat, 0, 0, 0);
    var bottom = addMesh(g, new THREE.ConeGeometry(24, 30, 14), rockMat, 0, -17, 0);
    bottom.rotation.x = Math.PI;
    // 散落的浮岩
    Noise.srand(88221);
    for (var fr = 0; fr < 8; fr++) {
      var fa = Noise.rand() * Math.PI * 2;
      var fr2 = 35 + Noise.rand() * 20;
      var f = addMesh(g, new THREE.DodecahedronGeometry(1.4 + Noise.rand() * 2.4, 0), rockMat,
        Math.cos(fa) * fr2, -2 - Noise.rand() * 16, Math.sin(fa) * fr2);
      f.rotation.set(Noise.rand() * 3, Noise.rand() * 3, Noise.rand() * 3);
    }
    // 草皮
    var soil = new THREE.Mesh(new THREE.CylinderGeometry(29.4, 29.4, 0.7, 18), stdMat(0x4a6a35, { roughness: 1 }));
    soil.position.y = 2.6;
    g.add(soil);

    // 星陨塔（岛心主塔）
    var towerMat = stdMat(0xe8e4d8, { roughness: 0.55 });
    addMesh(g, new THREE.CylinderGeometry(3.4, 5.2, 30, 12), towerMat, 0, 17.5, 0);
    addMesh(g, new THREE.CylinderGeometry(2.4, 3.4, 8, 12), towerMat, 0, 36, 0);
    addMesh(g, new THREE.ConeGeometry(3.3, 9, 12), stdMat(0xd9b45b, { metalness: 0.4, roughness: 0.4 }), 0, 43, 0);
    academyCrystal = new THREE.Mesh(
      new THREE.OctahedronGeometry(2.6),
      stdMat(0xbfefff, { emissive: 0x54d4f4, emissiveIntensity: 2, roughness: 0.2 })
    );
    academyCrystal.position.set(0, 50.5, 0);
    academyCrystal.scale.set(1, 1.7, 1);
    academyCrystal.castShadow = true;
    g.add(academyCrystal);
    addGlow(g, 0x8fe8ff, 24, 0.5, 0, 50.5, 0);

    // 四院尖塔（四角，各用本院色彩）
    var houses = [
      { c: 0xe8b45b, hex: '#e8b45b', a: Math.PI / 4 },       // 晨辉
      { c: 0x2f8a4a, hex: '#2f8a4a', a: Math.PI * 3 / 4 },    // 星语
      { c: 0xc97a4a, hex: '#c97a4a', a: Math.PI * 5 / 4 },    // 锤音
      { c: 0x4a9dc9, hex: '#4a9dc9', a: Math.PI * 7 / 4 }     // 海心
    ];
    for (var hi = 0; hi < houses.length; hi++) {
      var hv = houses[hi];
      var hx = Math.cos(hv.a) * 18, hz = Math.sin(hv.a) * 18;
      addMesh(g, new THREE.CylinderGeometry(1.9, 2.6, 15, 8), stdMat(0xe4e0d4, { roughness: 0.6 }), hx, 10, hz);
      addMesh(g, new THREE.ConeGeometry(2.7, 7, 8), stdMat(hv.c, { metalness: 0.35, roughness: 0.5 }), hx, 20, hz);
      var hb = addGlow(g, hv.c, 10, 0.42, hx, 23, hz);
      beacons.push({ sprite: hb, baseScale: 10, baseOpacity: 0.42, color: hv.hex });
      // 回廊（岛心 → 院塔）
      var len = 18 - 3;
      var walk = addMesh(g, new THREE.BoxGeometry(len, 0.7, 2.4), stdMat(0xcfc8b8, { roughness: 0.8 }),
        Math.cos(hv.a) * 9.5, 3.4, Math.sin(hv.a) * 9.5);
      walk.rotation.y = -hv.a + Math.PI / 2;
    }
    // 宿舍环（岛缘小屋）
    for (var dr = 0; dr < 12; dr++) {
      var da = dr / 12 * Math.PI * 2 + 0.26;
      if (Math.abs(Math.sin(da)) > 0.92 && Math.abs(Math.cos(da)) > 0.92) continue;
      var dx = Math.cos(da) * 25, dz = Math.sin(da) * 25;
      var dh = addMesh(g, new THREE.SphereGeometry(1.9, 8, 6), stdMat(0xe4ddcc), dx, 3.2, dz);
      dh.scale.set(1.15, 0.8, 1.15);
      var dr2 = addMesh(g, new THREE.ConeGeometry(2.2, 1.8, 8), stdMat(houses[dr % 4].c, { roughness: 0.6 }), dx, 5.4, dz);
      dr2.rotation.y = da;
    }
    // 星穗馆（圆顶图书馆）
    addMesh(g, new THREE.SphereGeometry(4.6, 14, 10, 0, Math.PI * 2, 0, Math.PI / 2),
      stdMat(0xd9b45b, { metalness: 0.45, roughness: 0.35 }), -11, 2.9, -13);
    addMesh(g, new THREE.CylinderGeometry(4.8, 5.1, 1.6, 14), stdMat(0xe8e4d8), -11, 3.2, -13);
    // 浮池（悬在岛缘、水不落的水池）
    var pool = new THREE.Mesh(
      new THREE.CircleGeometry(5.2, 24),
      new THREE.MeshStandardMaterial({ color: C(0x3a9dc0), roughness: 0.15, metalness: 0.1, emissive: C(0x1a4a66), emissiveIntensity: 0.5 })
    );
    pool.rotation.x = -Math.PI / 2;
    pool.position.set(13, 4.2, -11);
    g.add(pool);
    // 岛上小树
    for (var at = 0; at < 7; at++) {
      var aa = Noise.rand() * Math.PI * 2;
      var ar = 14 + Noise.rand() * 10;
      var ax = Math.cos(aa) * ar, az = Math.sin(aa) * ar;
      if (Math.hypot(ax, az) < 8) continue;
      addMesh(g, new THREE.CylinderGeometry(0.24, 0.4, 1.8, 5), stdMat(0x6b4a30), ax, 3.8, az);
      addMesh(g, new THREE.ConeGeometry(1.3, 3.0, 7), stdMat(0x245c34), ax, 6.4, az);
    }
    addGlow(g, 0x8fe8ff, 30, 0.3, 0, -14, 0);

    scene.add(g);
    academy = g;
  }

  /* ---------------- 星辉流（裂隙 → 各首都） ---------------- */

  function buildStreams() {
    var p0 = { x: RIFT_POS[0], z: RIFT_POS[1] };
    var start = new THREE.Vector3(p0.x, sampleH(p0.x, p0.z) + 6, p0.z);
    Noise.srand(666);
    for (var i = 0; i < CITIES.length; i++) {
      var c = CITIES[i];
      if ((c.tier || 'capital') !== 'capital') continue;
      if (c.id === 'sanctum') continue;
      var end = new THREE.Vector3(c._wx, c._y + 5, c._wz);
      var mid = start.clone().lerp(end, 0.5);
      mid.y = Math.max(start.y, end.y) + 20;
      var curve = new THREE.QuadraticBezierCurve3(start.clone(), mid, end.clone());
      var tubeMat = new THREE.MeshBasicMaterial({
        color: C(0x7fe8ff), transparent: true, opacity: 0.10,
        blending: THREE.AdditiveBlending, depthWrite: false
      });
      var tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 48, 0.6, 6, false), tubeMat);
      scene.add(tube);
      var n = 42;
      var geo = new THREE.BufferGeometry();
      var pos = new Float32Array(n * 3);
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      var ptMat = new THREE.PointsMaterial({
        color: C(0xbdf6ff), size: 1.8, map: glowTex, transparent: true, opacity: 0.85,
        blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true
      });
      var pts = new THREE.Points(geo, ptMat);
      pts.frustumCulled = false;
      scene.add(pts);
      streams.push({
        curve: curve, geo: geo, n: n, tubeMat: tubeMat, ptMat: ptMat,
        speed: 0.03 + Noise.rand() * 0.03, offset: Noise.rand()
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
      sunIntensity: 0.85, sunPos: [760, 350, 240],
      hemiSky: 0xc9b8d8, hemiGround: 0x6a5a4a, hemiIntensity: 0.55,
      fog: 0xd9b491, fogNear: 1100, fogFar: 4400,
      stars: 0.18, night: 0.15,
      waterDeep: 0x0d3d5c, waterShallow: 0x3a9dc0, waterSun: 0xffe3b8
    },
    noon: {
      zenith: 0x4a8fd9, horizon: 0xcfe8f5, sunDir: [0.35, 1.0, 0.25], sunColor: 0xfff5e0,
      sunIntensity: 1.0, sunPos: [380, 950, 280],
      hemiSky: 0xdceeff, hemiGround: 0x8a7a60, hemiIntensity: 0.64,
      fog: 0xcfe3ee, fogNear: 1400, fogFar: 5200,
      stars: 0, night: 0,
      waterDeep: 0x0d4a6e, waterShallow: 0x35a8d8, waterSun: 0xffffff
    },
    night: {
      zenith: 0x070b22, horizon: 0x1b2a52, sunDir: [-0.55, 0.75, -0.35], sunColor: 0x9fb4ff,
      sunIntensity: 0.5, sunPos: [-560, 760, -340],
      hemiSky: 0x33436e, hemiGround: 0x181828, hemiIntensity: 0.5,
      fog: 0x111832, fogNear: 900, fogFar: 4000,
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
    var best = null, bestD = 38;
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
    scene.fog = new THREE.Fog(0xd9b491, 1100, 4400);

    camera = new THREE.PerspectiveCamera(50, 1, 0.5, 12000);
    camera.position.copy(START_POS);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.target.copy(START_TGT);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 60;
    controls.maxDistance = 2400;
    controls.maxPolarAngle = 1.48;
    controls.minPolarAngle = 0.08;
    controls.autoRotateSpeed = 0.4;

    glowTex = makeGlowTexture();

    hemi = new THREE.HemisphereLight(0xc9b8d8, 0x6a5a4a, 0.65);
    scene.add(hemi);
    sun = new THREE.DirectionalLight(0xffd9a0, 1.0);
    sun.position.set(760, 350, 240);
    sun.castShadow = true;
    sun.shadow.mapSize.set(4096, 4096);
    sun.shadow.camera.left = -850;
    sun.shadow.camera.right = 850;
    sun.shadow.camera.top = 850;
    sun.shadow.camera.bottom = -850;
    sun.shadow.camera.near = 100;
    sun.shadow.camera.far = 3600;
    sun.shadow.bias = -0.0004;
    scene.add(sun);
    scene.add(sun.target);

    buildSky();
    buildStars();

    /* ---- 生成世界（地形模块：大陆/群岛/河流/湖泊/城市选址） ---- */
    var cityOpts = {
      whitecrown: { riverbank: true },
      greyport: { coast: true, minH: 1.5, maxH: 6 },
      shatterwave: { island: true, minH: 2, maxH: 9 },
      moltenheart: { minH: 5, maxH: 20 }
    };
    var cfgCities = CITIES.map(function (c) {
      var o = { id: c.id, x: c.anchor[0], z: c.anchor[1] };
      if (cityOpts[c.id]) for (var k in cityOpts[c.id]) o[k] = cityOpts[c.id][k];
      return o;
    });
    var built = Terrain.buildWorld({
      cities: cfgCities,
      rivers: RIVERS,
      lakes: LAKES
    });
    SIZE = built.size; SEG = built.seg; GRID = built.grid;
    H = built.H;
    riverMask = built.riverMask;
    riverPaths = built.riverPaths;
    for (var si = 0; si < built.citySites.length; si++) {
      var site = built.citySites[si];
      citySites.push({ wx: site.wx, wz: site.wz, y: site.y });
      for (var ci = 0; ci < CITIES.length; ci++) {
        if (CITIES[ci].id === site.id) {
          CITIES[ci]._wx = site.wx; CITIES[ci]._wz = site.wz; CITIES[ci]._y = site.y;
        }
      }
    }

    // 势力调色板
    for (var fi = 0; fi < FACTIONS.length; fi++) {
      PAL[FACTIONS[fi].id] = { low: new THREE.Color(FACTIONS[fi].low), high: new THREE.Color(FACTIONS[fi].high) };
    }

    buildWater();
    buildTerrain();
    buildVillages();
    buildTrees();
    buildCities();
    buildLandmarks();
    buildNecroShards();
    buildRift();
    buildAcademy();
    buildStreams();

    for (var j = 0; j < CITIES.length; j++) {
      var cd = CITIES[j];
      cities3D.push({ data: cd, wx: cd._wx, wz: cd._wz, y: cd._y });
    }
    // 星槎空岛也是可点击目标
    cities3D.push({
      data: {
        id: 'academy', name: '星槎学院', tier: 'academy', faction: null,
        title: '裂隙上空 · 万族最高学府', pop: '学生 400 · 师长 41',
        lore: ACADEMY.motto
      },
      wx: RIFT_POS[0], wz: RIFT_POS[1], y: academyBaseY + 12
    });

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
    if (academy) {
      academy.position.y = academyBaseY + Math.sin(t * 0.4) * 1.5;
      if (academyCrystal) academyCrystal.rotation.y = t * 0.6;
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
      t: 0, dur: 1.8
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
      var d;
      if (c.id === 'academy') d = 190;
      else if ((c.tier || 'capital') === 'capital') d = c.id === 'whitecrown' ? 260 : 200;
      else if (c.tier === 'city') d = 150;
      else if (c.tier === 'town') d = 115;
      else d = 90;
      flyTo(new THREE.Vector3(c._wx, c._y + 4, c._wz), d);
    },
    flyToFaction: function (f) {
      var y = Math.max(sampleH(f.cx, f.cz), 6);
      var dist = Math.max(260, Math.min(640, f.r * 2.6));
      flyTo(new THREE.Vector3(f.cx, y + 6, f.cz), dist);
    },
    flyToAcademy: function () {
      if (!academy) return;
      flyTo(new THREE.Vector3(RIFT_POS[0], academyBaseY + 14, RIFT_POS[1]), 200);
    },
    resetView: function () {
      fly = {
        fromPos: camera.position.clone(),
        toPos: START_POS.clone(),
        fromTgt: controls.target.clone(),
        toTgt: START_TGT.clone(),
        t: 0, dur: 1.8
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
