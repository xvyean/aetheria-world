/* ============================================================
 * 星槎学院 · 独立 3D 观览器
 * 载入 Blender 导出的 models/xingcha_academy.glb（Draco）
 * - 天空 / 云海 / 星空 / 三档氛围（晨 · 午 · 星夜）
 * - 陪岛石公转、裂隙晶自转、渡船潮汐往返、火/灯/窗呼吸、旗帜摆动
 * - 建筑热点：悬停高亮、点击飞入 + 志书卡片
 * Three.js r128
 * ============================================================ */

var Academy3D = (function () {
  'use strict';

  var canvas, renderer, scene, camera, controls;
  var root = null;          // GLB 根节点（岛 + 一切）
  var skyMesh, skyMat, starPts, starMat, beamMesh, beamMat;
  var sun, hemi, riftLight, crystalLight;
  var clock = new THREE.Clock();
  var W = 1, H = 1;
  var ready = false;
  var onHoverCb = null, onPickCb = null, onReadyCb = null, onProgressCb = null, onFrameCb = null;
  var occluders = [];       // 用于地名遮挡判断的大体块（岛体、塔身、大屋）
  var raycaster = new THREE.Raycaster();
  var hotspots = [];
  var hovered = null;
  var mouse = { x: -1e4, y: -1e4, down: null };
  var fly = null;
  var currentPreset = 'dawn';
  var presetTween = null;
  var atmo = null;
  var autoRotate = false;
  var GROUND = 1.75;

  // 动画对象
  var anim = { stones: [], crystal: null, shards: [], halo: null, fire: [], lamps: [], windows: [], banners: [], smoke: [], clouds: [],
               ferry: [], ferryTop: null, water: null, orbs: [], mist: [], armillary: null, beam: null, moss: [], foliage: [], net: null,
               crystalRoot: [], bell: null };
  var ferryState = { t: 0.0, dir: 1 };
  var emissiveBase = new Map();

  var PRESETS = {
    dawn: { zenith: 0x2b4aa6, horizon: 0xf1bd8e, low: 0x6f7d98, sunDir: [-0.42, 0.36, -0.83], sunColor: 0xffd2a0, sunI: 3.0,
            hemiSky: 0xcfd6f0, hemiGround: 0x7a6e5c, hemiI: 0.7, fog: 0xdcc3b4, fogNear: 720, fogFar: 2600, stars: 0.12, night: 0.10, exposure: 1.12 },
    noon: { zenith: 0x1f6fd0, horizon: 0xd8ecf9, low: 0x8593a8, sunDir: [-0.30, 0.88, -0.36], sunColor: 0xfff5e3, sunI: 3.2,
            hemiSky: 0xe4f1ff, hemiGround: 0x9a8f7b, hemiI: 0.72, fog: 0xdbe8f2, fogNear: 820, fogFar: 2800, stars: 0, night: 0, exposure: 1.1 },
    night: { zenith: 0x040613, horizon: 0x1a2350, low: 0x0a0e22, sunDir: [-0.55, 0.55, 0.62], sunColor: 0x8fa4ff, sunI: 0.6,
             hemiSky: 0x2a3560, hemiGround: 0x101020, hemiI: 0.5, fog: 0x0c1230, fogNear: 620, fogFar: 2200, stars: 1, night: 1, exposure: 1.0 }
  };

  var START_POS = new THREE.Vector3(-520, 285, 425);
  var START_TGT = new THREE.Vector3(0, 12, 0);

  function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

  /* ---------------- 天空 ---------------- */
  function buildSky() {
    skyMat = new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false, fog: false,
      uniforms: {
        uZenith: { value: new THREE.Color(0x3a4f9e) }, uHorizon: { value: new THREE.Color(0xf2b989) }, uLow: { value: new THREE.Color(0x3b3f4e) },
        uSunDir: { value: new THREE.Vector3(0.55, 0.35, -0.75).normalize() }, uSunColor: { value: new THREE.Color(0xffd7a3) },
        uNight: { value: 0.12 }, uTime: { value: 0 }, uCloudY: { value: -300.0 }
      },
      // 方向取「相机 → 天球顶点」，这样云海平面的透视和视差是对的
      vertexShader: 'varying vec3 vDir; void main(){ vec4 wp = modelMatrix * vec4(position,1.0); vDir = wp.xyz - cameraPosition; gl_Position = projectionMatrix * viewMatrix * wp; }',
      fragmentShader: [
        'uniform vec3 uZenith, uHorizon, uLow, uSunDir, uSunColor; uniform float uNight, uTime, uCloudY; varying vec3 vDir;',
        'float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }',
        'float noise(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f); return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y); }',
        'float fbm(vec2 p){ float v = 0.0, a = 0.5; mat2 m = mat2(1.6, 1.2, -1.2, 1.6); for (int i = 0; i < 5; i++) { v += a * noise(p); p = m * p; a *= 0.5; } return v; }',
        'void main(){',
        '  vec3 d = normalize(vDir); float y = d.y;',
        '  float s = max(dot(d, uSunDir), 0.0);',
        '  // 天：地平线暖带 → 天顶；带一点日晕',
        '  float up = smoothstep(0.0, 0.42, y); up = pow(up, 0.62);',
        '  vec3 sky = mix(uHorizon, uZenith, up);',
        '  // 高层卷云（很淡）',
        '  if (y > 0.02) { vec2 cu = d.xz / (y + 0.15) * 1.4 + vec2(uTime * 0.003, 0.0); float ci = fbm(cu) ; ci = smoothstep(0.55, 0.85, ci) * smoothstep(0.02, 0.25, y) * 0.35; sky = mix(sky, mix(uHorizon, vec3(1.0), 0.5) * (1.0 - uNight * 0.7), ci); }',
        '  vec3 c = sky;',
        '  // 地平线之下：薄霭 + 云海平面',
        '  if (y < 0.0) {',
        '    vec3 haze = mix(uHorizon, uLow, smoothstep(0.0, 0.45, -y));',
        '    c = haze;',
        '    if (y < -0.004) {',
        '      float t = (uCloudY - cameraPosition.y) / y;',
        '      vec2 p = cameraPosition.xz + d.xz * t;',
        '      vec2 uv = p * 0.0032 + vec2(uTime * 0.006, uTime * 0.002);',
        '      float n = fbm(uv);',
        '      float n2 = fbm(uv + normalize(uSunDir.xz + vec2(1e-4)) * 0.06);',
        '      float dens = smoothstep(0.38, 0.72, n);',
        '      float lit = clamp((n - n2) * 9.0 + 0.55, 0.0, 1.0);',
        '      vec3 shadowCol = mix(uLow, uHorizon, 0.35) * (1.0 - uNight * 0.6);',
        '      vec3 litCol = mix(vec3(1.0, 0.98, 0.96), uSunColor, 0.35) * (1.0 - uNight * 0.78) + uNight * vec3(0.10, 0.12, 0.22);',
        '      vec3 cloud = mix(shadowCol, litCol, lit);',
        '      float fogF = 1.0 - exp(-t * 0.00085);',
        '      cloud = mix(cloud, haze, fogF);',
        '      float thin = 1.0 - dens;',
        '      vec3 gap = mix(uLow * 0.85, haze, fogF);',
        '      c = mix(gap, cloud, dens * 0.92 + 0.08);',
        '    }',
        '  }',
        '  float glow = (pow(s, 8.0) * 0.22 + pow(s, 64.0) * 0.7 + pow(s, 900.0) * 4.0) * (1.0 - uNight * 0.85);',
        '  c += uSunColor * glow * (y < 0.0 ? smoothstep(-0.12, 0.0, y) : 1.0);',
        '  gl_FragColor = vec4(c, 1.0);',
        '}'
      ].join('\n')
    });
    skyMesh = new THREE.Mesh(new THREE.SphereGeometry(1800, 48, 32), skyMat);
    scene.add(skyMesh);
    // 星空
    var N = 2600, pos = new Float32Array(N * 3), sz = new Float32Array(N);
    var seed = 7;
    function rnd() { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; }
    for (var i = 0; i < N; i++) {
      var u = rnd() * 2 - 1, th = rnd() * Math.PI * 2, r = Math.sqrt(1 - u * u);
      var yy = Math.abs(u) * 0.95 + 0.05;
      pos[i * 3] = r * Math.cos(th) * 1600; pos[i * 3 + 1] = yy * 1600; pos[i * 3 + 2] = r * Math.sin(th) * 1600;
      sz[i] = 1 + rnd() * 2.5;
    }
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aSize', new THREE.BufferAttribute(sz, 1));
    starMat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, fog: false, blending: THREE.AdditiveBlending,
      uniforms: { uOpacity: { value: 0.15 }, uTime: { value: 0 } },
      vertexShader: 'attribute float aSize; varying float vA; uniform float uTime; void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aSize * 1.6; vA = 0.6 + 0.4 * sin(uTime * 1.3 + position.x * 0.01 + position.z * 0.013); }',
      fragmentShader: 'uniform float uOpacity; varying float vA; void main(){ vec2 c = gl_PointCoord - 0.5; float d = length(c); if (d > 0.5) discard; float a = smoothstep(0.5, 0.05, d); gl_FragColor = vec4(1.0, 0.97, 0.9, a * uOpacity * vA); }'
    });
    starPts = new THREE.Points(g, starMat);
    scene.add(starPts);
  }

  /* ---------------- 裂隙光柱（塔根下，从裂隙直上） ---------------- */
  function buildBeam() {
    beamMat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
      uniforms: { uTime: { value: 0 }, uColor: { value: new THREE.Color(0x7fdcff) }, uNight: { value: 0.1 } },
      vertexShader: 'varying vec2 vUv; varying vec3 vN; varying vec3 vV; void main(){ vUv = uv; vN = normalize(normalMatrix * normal); vec4 mv = modelViewMatrix * vec4(position,1.0); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }',
      fragmentShader: [
        'uniform float uTime, uNight; uniform vec3 uColor; varying vec2 vUv; varying vec3 vN; varying vec3 vV;',
        'void main(){',
        '  float rim = 1.0 - abs(dot(normalize(vN), normalize(vV)));',
        '  float flow = 0.5 + 0.5 * sin(vUv.y * 40.0 - uTime * 2.5 + sin(vUv.x * 30.0) * 2.0);',
        '  float fade = smoothstep(0.0, 0.25, vUv.y) * smoothstep(1.0, 0.55, vUv.y);',
        '  float a = (0.025 + 0.32 * pow(rim, 2.2) + 0.05 * flow * rim) * fade * (0.8 + uNight * 0.9);',
        '  gl_FragColor = vec4(uColor * (1.0 + flow * 0.4), a);',
        '}'
      ].join('\n')
    });
    var geo = new THREE.CylinderGeometry(7.5, 16, 420, 32, 1, true);
    beamMesh = new THREE.Mesh(geo, beamMat);
    beamMesh.position.set(0, -40 - 210 + 30, 0);
    scene.add(beamMesh);
    // 上升粒子
    var N = 500, pos = new Float32Array(N * 3), off = new Float32Array(N);
    for (var i = 0; i < N; i++) {
      var a = Math.random() * Math.PI * 2, r = 3 + Math.random() * 11;
      pos[i * 3] = Math.cos(a) * r; pos[i * 3 + 1] = -420 + Math.random() * 420; pos[i * 3 + 2] = Math.sin(a) * r;
      off[i] = Math.random();
    }
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aOff', new THREE.BufferAttribute(off, 1));
    var pm = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uTime: { value: 0 } },
      vertexShader: 'attribute float aOff; varying float vA; uniform float uTime; void main(){ vec3 p = position; p.y = -430.0 + mod(p.y + 430.0 + uTime * (6.0 + aOff * 9.0), 440.0); p.x += sin(uTime * 0.7 + aOff * 20.0) * 1.2; vec4 mv = modelViewMatrix * vec4(p,1.0); gl_Position = projectionMatrix * mv; gl_PointSize = (2.0 + aOff * 4.0) * 180.0 / -mv.z; vA = smoothstep(-430.0, -380.0, p.y) * smoothstep(10.0, -40.0, p.y); }',
      fragmentShader: 'varying float vA; void main(){ float d = length(gl_PointCoord - 0.5); if (d > 0.5) discard; gl_FragColor = vec4(0.6, 0.9, 1.0, smoothstep(0.5, 0.0, d) * vA * 0.9); }'
    });
    var pts = new THREE.Points(g, pm);
    pts.position.set(0, 0, 0);
    scene.add(pts);
    anim.beamParticles = pm;
  }

  /* ---------------- 载入 GLB ---------------- */
  function loadModel(url, hotspotUrl) {
    var loader = new THREE.GLTFLoader();
    var draco = new THREE.DRACOLoader();
    draco.setDecoderPath('vendor/draco/');
    draco.setDecoderConfig({ type: 'js' });
    loader.setDRACOLoader(draco);
    loader.load(url, function (gltf) {
      root = gltf.scene;
      root.traverse(function (o) {
        if (!o.isMesh) return;
        o.castShadow = true;
        o.receiveShadow = true;
        var m = o.material;
        if (m) {
          m.vertexColors = m.vertexColors || (o.geometry.attributes.color !== undefined);
          if (m.emissive && m.emissiveIntensity > 0) emissiveBase.set(o.uuid, m.emissiveIntensity);
          if (m.transparent) { o.castShadow = false; }
        }
        classify(o);
        var nm = (o.name || '');
        if (/^(island|tower|library|hall|dawn|speak|forge|tide|citywall|scholar|residence|service|garden)_/i.test(nm) && o.geometry && o.geometry.attributes.position && o.geometry.attributes.position.count > 400 && !o.userData.fx) {
          occluders.push(o);
        }
      });
      scene.add(root);
      if (hotspotUrl) {
        fetch(hotspotUrl).then(function (r) { return r.json(); }).then(function (js) {
          setupHotspots(js.hotspots || []);
          finishLoad();
        }).catch(function () { finishLoad(); });
      } else finishLoad();
    }, function (ev) {
      if (onProgressCb && ev.total) onProgressCb(ev.loaded / ev.total);
    }, function (err) {
      console.error('GLB load failed', err);
      var el = document.getElementById('academy-loading');
      if (el) el.textContent = '模型载入失败：' + (err && err.message ? err.message : err);
    });
  }

  function finishLoad() {
    ready = true;
    if (onReadyCb) onReadyCb();
  }

  function classify(o) {
    var fx = o.userData.fx;
    var name = o.name || '';
    var m = o.material;
    if (o.userData.orbit_r !== undefined) {
      anim.stones.push({ m: o, r: o.userData.orbit_r, a0: o.userData.orbit_a0, y: o.position.y, spin: o.userData.spin || 0, bob: o.userData.bob || 1, isShard: fx === 'shard' });
      return;
    }
    if (!fx) return;
    switch (fx) {
      case 'crystal': anim.crystal = o; if (m) { m.emissiveIntensity = 3.0; m.toneMapped = false; } break;
      case 'halo': anim.halo = o; break;
      case 'fire': anim.fire.push(o); if (m) m.emissiveIntensity = 2.5; break;
      case 'lamp': case 'lamp_main': anim.lamps.push(o); if (m) m.emissiveIntensity = fx === 'lamp_main' ? 3.0 : 1.4; break;
      case 'window': anim.windows.push(o); if (m) m.emissiveIntensity = 0.5; break;
      case 'banner': case 'flag': anim.banners.push({ m: o, base: o.geometry.attributes.position.array.slice(0), phase: Math.random() * 6 }); break;
      case 'smoke': anim.smoke.push({ m: o, i: o.userData.fx_i || 0, base: o.position.clone(), s: o.scale.clone() }); if (m) { m.depthWrite = false; } break;
      case 'cloud': anim.clouds.push({ m: o, base: o.position.clone(), i: o.userData.fx_i || 0 }); if (m) { m.depthWrite = false; } break;
      case 'ferry': anim.ferry.push(o); break;
      case 'water': anim.water = o; if (m) { m.depthWrite = false; } break;
      case 'waterfall': if (m) { m.depthWrite = false; } break;
      case 'orb': anim.orbs.push({ m: o, base: o.position.clone(), i: o.userData.fx_i || 0 }); break;
      case 'mist': anim.mist.push({ m: o, base: o.position.clone(), s: o.scale.clone(), i: o.userData.fx_i || 0 }); if (m) { m.depthWrite = false; } break;
      case 'armillary': anim.armillary = o; break;
      case 'beam': o.visible = false; break;   // 用 shader 光柱替代
      case 'moss': anim.moss.push(o); if (m) m.emissiveIntensity = 0.8; break;
      case 'crystal_root': anim.crystalRoot.push(o); if (m) m.emissiveIntensity = 1.5; break;
      case 'foliage': anim.foliage.push({ m: o, base: o.geometry.attributes.position.array.slice(0), phase: Math.random() * 6 }); break;
      case 'net': anim.net = o; if (m) { m.depthWrite = false; m.side = THREE.DoubleSide; } break;
      case 'bell': anim.bell = o; break;
    }
  }

  /* ---------------- 热点 ---------------- */
  function setupHotspots(list) {
    hotspots = list.map(function (h) {
      // Blender Z-up → three Y-up: (x, y, z) → (x, z, -y)
      return { key: h.key, name: h.name, pos: new THREE.Vector3(h.pos[0], h.pos[2], -h.pos[1]), r: h.r, cam: h.cam ? new THREE.Vector3(h.cam[0], h.cam[2], -h.cam[1]) : null };
    });
  }

  function updateHover() {
    if (!ready) return;
    var best = null, bestD = 40;
    var tmp = new THREE.Vector3();
    for (var i = 0; i < hotspots.length; i++) {
      var h = hotspots[i];
      tmp.copy(h.pos).project(camera);
      if (tmp.z > 1) continue;
      var sx = (tmp.x * 0.5 + 0.5) * W, sy = (-tmp.y * 0.5 + 0.5) * H;
      var d = Math.hypot(mouse.x - sx, mouse.y - sy);
      // 距离越远的热点判定半径按屏幕尺寸缩放
      var dist = camera.position.distanceTo(h.pos);
      var rad = Math.max(18, Math.min(60, h.r * 900 / dist));
      if (d < rad && d < bestD + (rad - 40)) { bestD = d; best = h; }
    }
    if (best !== hovered) {
      hovered = best;
      canvas.style.cursor = best ? 'pointer' : 'grab';
      if (onHoverCb) onHoverCb(best ? best.key : null, best);
    }
  }

  var _projFrame = 0;
  function projectHotspots() {
    // 供 UI 层画标签：返回 [{key, name, x, y, visible, occluded, dist}]
    var out = [];
    var tmp = new THREE.Vector3(), dir = new THREE.Vector3();
    _projFrame++;
    for (var i = 0; i < hotspots.length; i++) {
      var h = hotspots[i];
      tmp.copy(h.pos).project(camera);
      var vis = tmp.z < 1 && Math.abs(tmp.x) < 1.05 && Math.abs(tmp.y) < 1.05;
      var dist = camera.position.distanceTo(h.pos);
      // 遮挡：每 6 帧对每个可见热点做一次射线检测（只对大体块）
      if (vis && occluders.length && ((_projFrame + i) % 6 === 0)) {
        dir.copy(h.pos).sub(camera.position).normalize();
        raycaster.set(camera.position, dir);
        raycaster.far = dist - Math.max(1.5, h.r * 0.9);
        h.occluded = raycaster.intersectObjects(occluders, false).length > 0;
      }
      out.push({ key: h.key, name: h.name, x: (tmp.x * 0.5 + 0.5) * W, y: (-tmp.y * 0.5 + 0.5) * H, visible: vis, occluded: !!h.occluded, dist: dist });
    }
    return out;
  }

  /* ---------------- 氛围 ---------------- */
  function makeState(p) {
    return { zenith: new THREE.Color(p.zenith), horizon: new THREE.Color(p.horizon), low: new THREE.Color(p.low),
      sunDir: new THREE.Vector3().fromArray(p.sunDir).normalize(), sunColor: new THREE.Color(p.sunColor), sunI: p.sunI,
      hemiSky: new THREE.Color(p.hemiSky), hemiGround: new THREE.Color(p.hemiGround), hemiI: p.hemiI,
      fog: new THREE.Color(p.fog), fogNear: p.fogNear, fogFar: p.fogFar, stars: p.stars, night: p.night, exposure: p.exposure };
  }
  function cloneState(s) { var o = {}; for (var k in s) o[k] = (s[k] && s[k].clone) ? s[k].clone() : s[k]; return o; }
  function lerpState(cur, a, b, k) {
    for (var key in cur) {
      if (cur[key] && cur[key].isColor) cur[key].copy(a[key]).lerp(b[key], k);
      else if (cur[key] && cur[key].isVector3) cur[key].copy(a[key]).lerp(b[key], k).normalize();
      else cur[key] = a[key] + (b[key] - a[key]) * k;
    }
  }
  function applyAtmosphere() {
    skyMat.uniforms.uZenith.value.copy(atmo.zenith); skyMat.uniforms.uHorizon.value.copy(atmo.horizon); skyMat.uniforms.uLow.value.copy(atmo.low);
    skyMat.uniforms.uSunDir.value.copy(atmo.sunDir); skyMat.uniforms.uSunColor.value.copy(atmo.sunColor); skyMat.uniforms.uNight.value = atmo.night;
    sun.position.copy(atmo.sunDir).multiplyScalar(300); sun.color.copy(atmo.sunColor); sun.intensity = atmo.sunI;
    sun.shadow.camera.updateProjectionMatrix();
    hemi.color.copy(atmo.hemiSky); hemi.groundColor.copy(atmo.hemiGround); hemi.intensity = atmo.hemiI;
    scene.fog.color.copy(atmo.fog); scene.fog.near = atmo.fogNear; scene.fog.far = atmo.fogFar;
    starMat.uniforms.uOpacity.value = atmo.stars;
    beamMat.uniforms.uNight.value = atmo.night;
    renderer.toneMappingExposure = atmo.exposure;
    var n = atmo.night;
    riftLight.intensity = 1.2 + n * 2.0;
    crystalLight.intensity = 1.5 + n * 3.0;
    var i;
    for (i = 0; i < anim.windows.length; i++) anim.windows[i].material.emissiveIntensity = 0.35 + n * 2.2;
    for (i = 0; i < anim.lamps.length; i++) anim.lamps[i].material.emissiveIntensity = (anim.lamps[i].userData.fx === 'lamp_main' ? 2.5 : 1.0) + n * 3.0;
    for (i = 0; i < anim.moss.length; i++) anim.moss[i].material.emissiveIntensity = 0.5 + n * 2.5;
    for (i = 0; i < anim.crystalRoot.length; i++) anim.crystalRoot[i].material.emissiveIntensity = 1.2 + n * 2.5;
  }

  /* ---------------- 动画 ---------------- */
  function updateAnim(t, dt) {
    var i, o;
    // 陪岛石：绕岛一年一周（这里 1 圈 ≈ 200 s），自转 + 起伏
    for (i = 0; i < anim.stones.length; i++) {
      o = anim.stones[i];
      if (o.isShard) {
        var a = o.a0 + t * 0.6;
        o.m.position.set(Math.cos(a) * o.r, o.y + Math.sin(t * 1.7 + o.a0 * 3) * 0.25, -Math.sin(a) * o.r);
        o.m.rotation.y += dt * 1.2;
      } else {
        var a2 = o.a0 + t * (Math.PI * 2 / 200);
        o.m.position.set(Math.cos(a2) * o.r, o.y + Math.sin(t * 0.35 + o.a0 * 2) * o.bob, -Math.sin(a2) * o.r);
        o.m.rotation.y += dt * o.spin * 0.25;
      }
    }
    // 裂隙晶：自转 + 呼吸
    if (anim.crystal) {
      anim.crystal.rotation.y = t * 0.5;
      var s = 1 + Math.sin(t * 1.3) * 0.04;
      anim.crystal.scale.set(s, s * 1.3, s);
      anim.crystal.material.emissiveIntensity = 2.6 + Math.sin(t * 1.3) * 0.7 + atmo.night * 1.5;
      crystalLight.intensity = 1.5 + atmo.night * 3.0 + Math.sin(t * 1.3) * 0.5;
    }
    if (anim.halo) { anim.halo.rotation.y = -t * 0.3; anim.halo.rotation.x = Math.sin(t * 0.4) * 0.15; }
    // 火：抖动缩放
    for (i = 0; i < anim.fire.length; i++) {
      o = anim.fire[i];
      var f = 1 + Math.sin(t * 9 + i) * 0.06 + Math.sin(t * 17 + i * 2) * 0.04;
      o.scale.set(f, 1 + Math.sin(t * 11 + i) * 0.1, f);
      o.material.emissiveIntensity = 2.2 + Math.sin(t * 13 + i) * 0.5 + atmo.night * 1.0;
    }
    // 旗帜：顶点波动（把原始位置沿法向/横向偏移）
    for (i = 0; i < anim.banners.length; i++) {
      o = anim.banners[i];
      var arr = o.m.geometry.attributes.position.array, b = o.base;
      for (var v = 0; v < arr.length; v += 3) {
        var yy = b[v + 1];
        var k = Math.max(0, 1 - (yy - o.m.geometry.boundingBox.min.y) / 4); // 越往下摆得越大（geometry 局部）
        arr[v] = b[v] + Math.sin(t * 2.4 + yy * 2.2 + o.phase) * 0.09 * (0.3 + k);
        arr[v + 2] = b[v + 2] + Math.cos(t * 2.0 + yy * 1.7 + o.phase) * 0.07 * (0.3 + k);
      }
      o.m.geometry.attributes.position.needsUpdate = true;
    }
    // 烟：上升、扩散、循环
    for (i = 0; i < anim.smoke.length; i++) {
      o = anim.smoke[i];
      var ph = (t * 0.25 + o.i * 0.17) % 1;
      o.m.position.set(o.base.x + Math.sin(t * 0.5 + o.i) * 0.6 * ph, o.base.y + ph * 5.0, o.base.z + Math.cos(t * 0.4 + o.i) * 0.5 * ph);
      var ss = 0.6 + ph * 1.6;
      o.m.scale.set(o.s.x * ss, o.s.y * ss, o.s.z * ss);
      o.m.material.opacity = 0.32 * (1 - ph) * (1 - ph * 0.3);
    }
    for (i = 0; i < anim.mist.length; i++) {
      o = anim.mist[i];
      var mp = (t * 0.35 + o.i * 0.3) % 1;
      o.m.position.set(o.base.x, o.base.y - mp * 6, o.base.z);
      var ms = 0.8 + mp * 1.8;
      o.m.scale.set(o.s.x * ms, o.s.y * ms * 0.6, o.s.z * ms);
      o.m.material.opacity = 0.3 * (1 - mp);
    }
    // 云：慢漂
    for (i = 0; i < anim.clouds.length; i++) {
      o = anim.clouds[i];
      o.m.position.x = o.base.x + Math.sin(t * 0.05 + o.i) * 6;
      o.m.position.z = o.base.z + Math.cos(t * 0.04 + o.i * 1.3) * 5;
      o.m.position.y = o.base.y + Math.sin(t * 0.1 + o.i) * 0.8;
    }
    // 水球：漂浮
    for (i = 0; i < anim.orbs.length; i++) {
      o = anim.orbs[i];
      o.m.position.y = o.base.y + Math.sin(t * 1.1 + o.i * 2.1) * 0.35;
      o.m.position.x = o.base.x + Math.sin(t * 0.6 + o.i) * 0.2;
    }
    if (anim.armillary) anim.armillary.rotation.z = t * 0.12;
    if (anim.water) { anim.water.material.opacity = 0.78 + Math.sin(t * 1.5) * 0.06; }
    if (anim.bell) anim.bell.rotation.x = Math.sin(t * 2.6) * 0.06 * Math.max(0, Math.sin(t * 0.15));
    if (anim.net) anim.net.position.x = Math.sin(t * 0.8) * 0.06;
    // 渡船：顺光潮上下往返（-300 → 0），停靠时停 20 s
    var cycle = 90.0, T = t % cycle;
    var yoff;
    if (T < 30) yoff = -300 * (1 - ease(T / 30));            // 上升
    else if (T < 50) yoff = 0;                                 // 停在槎埠
    else if (T < 80) yoff = -300 * ease((T - 50) / 30);        // 下降
    else yoff = -300;                                          // 停在旧校
    var sway = Math.sin(t * 0.9) * 0.15;
    for (i = 0; i < anim.ferry.length; i++) {
      o = anim.ferry[i];
      if (!o.userData._base) o.userData._base = o.position.clone();
      o.position.y = o.userData._base.y + yoff + sway;
      o.rotation.z = Math.sin(t * 0.7) * 0.012;
    }
    // 岛整体呼吸（随潮汐轻轻起伏）
    if (root) root.position.y = Math.sin(t * 0.25) * 0.6;
    // 树叶：轻微摇动（改缩放比顶点更省）
    for (i = 0; i < anim.foliage.length; i++) {
      o = anim.foliage[i];
      var sw = 1 + Math.sin(t * 1.1 + o.phase) * 0.012;
      o.m.scale.set(o.m.scale.x < 0 ? -sw : sw, o.m.scale.y, sw);
    }
    // 光柱
    beamMat.uniforms.uTime.value = t;
    if (anim.beamParticles) anim.beamParticles.uniforms.uTime.value = t;
    skyMat.uniforms.uTime.value = t;
    starMat.uniforms.uTime.value = t;
  }

  /* ---------------- 初始化 ---------------- */
  function init(opts) {
    opts = opts || {};
    canvas = document.getElementById(opts.canvasId || 'academy-canvas');
    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.physicallyCorrectLights = false;

    scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0xe0bfa0, 220, 900);
    camera = new THREE.PerspectiveCamera(42, 1, 0.3, 4000);
    camera.position.copy(START_POS);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.target.copy(START_TGT);
    controls.enableDamping = true; controls.dampingFactor = 0.07;
    controls.minDistance = 6; controls.maxDistance = 1400;
    controls.maxPolarAngle = Math.PI * 0.92; controls.minPolarAngle = 0.05;
    controls.autoRotateSpeed = 0.5;

    hemi = new THREE.HemisphereLight(0xbfc4e0, 0x6b6152, 0.55); scene.add(hemi);
    sun = new THREE.DirectionalLight(0xffd7a3, 2.6);
    sun.position.set(520, 410, -680);
    sun.castShadow = true;
    sun.shadow.mapSize.set(4096, 4096);
    sun.shadow.camera.left = -310; sun.shadow.camera.right = 310; sun.shadow.camera.top = 310; sun.shadow.camera.bottom = -310;
    sun.shadow.camera.near = 80; sun.shadow.camera.far = 1800;
    sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.03;
    scene.add(sun); scene.add(sun.target);
    riftLight = new THREE.PointLight(0x6fd0ff, 1.2, 360, 1.6); riftLight.position.set(0, -118, 0); scene.add(riftLight);
    crystalLight = new THREE.PointLight(0x9fe6ff, 1.5, 70, 1.8); crystalLight.position.set(0, 44.5, 0); scene.add(crystalLight);

    buildSky();
    buildBeam();
    atmo = makeState(PRESETS.dawn);
    applyAtmosphere();

    loadModel(opts.model || 'models/xingcha_academy.glb', opts.hotspots || 'models/xingcha_academy.hotspots.json');

    resize();
    window.addEventListener('resize', resize);
    canvas.addEventListener('pointermove', function (e) { var r = canvas.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; });
    canvas.addEventListener('pointerdown', function (e) { mouse.down = [e.clientX, e.clientY]; });
    canvas.addEventListener('click', function (e) {
      if (!mouse.down) return;
      var dx = e.clientX - mouse.down[0], dy = e.clientY - mouse.down[1];
      if (dx * dx + dy * dy < 36 && onPickCb) onPickCb(hovered ? hovered.key : null, hovered);
      mouse.down = null;
    });
    animate();
  }

  function resize() {
    var parent = canvas ? canvas.parentElement : null;
    if (!parent) return;
    var w = parent.clientWidth, h = parent.clientHeight;
    if (!w || !h) return;
    W = w; H = h;
    renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }

  var visible = true;
  function animate() {
    requestAnimationFrame(animate);
    var rawDt = clock.getDelta();
    var dt = Math.min(rawDt, 0.1);          // 场景动画用（慢机器上不跳帧）
    var wall = Math.min(rawDt, 1.0);        // 相机/氛围过渡用真实时间，帧率再低也按时到达
    var t = clock.elapsedTime;
    if (!visible) return;
    if (fly) {
      fly.t += wall / fly.dur;
      var k = fly.t >= 1 ? 1 : ease(fly.t);
      camera.position.lerpVectors(fly.from, fly.to, k);
      controls.target.lerpVectors(fly.fromT, fly.toT, k);
      if (fly.t >= 1) { fly = null; if (autoRotate) controls.autoRotate = true; }
    }
    controls.update();
    if (presetTween) {
      presetTween.t += wall / presetTween.dur;
      var kk = presetTween.t >= 1 ? 1 : ease(presetTween.t);
      lerpState(atmo, presetTween.from, presetTween.to, kk);
      if (presetTween.t >= 1) presetTween = null;
      applyAtmosphere();
    }
    if (ready) updateAnim(t, dt);
    renderer.render(scene, camera);
    updateHover();
    if (onFrameCb) onFrameCb(t);
  }

  function flyTo(pos, tgt, dur) {
    fly = { from: camera.position.clone(), to: pos.clone(), fromT: controls.target.clone(), toT: tgt.clone(), t: 0, dur: dur || 1.8 };
    if (controls.autoRotate) { controls.autoRotate = false; }
  }

  return {
    init: init,
    resize: resize,
    setVisible: function (v) { visible = v; if (v) { clock.getDelta(); resize(); } },
    setPreset: function (name) {
      if (!PRESETS[name] || name === currentPreset) return;
      presetTween = { from: cloneState(atmo), to: makeState(PRESETS[name]), t: 0, dur: 2.0 };
      currentPreset = name;
    },
    getPreset: function () { return currentPreset; },
    flyToHotspot: function (key) {
      for (var i = 0; i < hotspots.length; i++) {
        var h = hotspots[i];
        if (h.key !== key) continue;
        var cam = h.cam ? h.cam.clone() : h.pos.clone().add(new THREE.Vector3(18, 10, 18));
        flyTo(cam, h.pos.clone(), 2.0);
        return true;
      }
      return false;
    },
    flyHome: function () { flyTo(START_POS, START_TGT, 2.0); },
    flyUnder: function () { flyTo(new THREE.Vector3(260, -220, 330), new THREE.Vector3(0, -72, 0), 2.4); },
    setAutoRotate: function (b) { autoRotate = b; controls.autoRotate = b; },
    getAutoRotate: function () { return autoRotate; },
    projectHotspots: projectHotspots,
    onHover: function (cb) { onHoverCb = cb; },
    onPick: function (cb) { onPickCb = cb; },
    onReady: function (cb) { onReadyCb = cb; if (ready) cb(); },
    onProgress: function (cb) { onProgressCb = cb; },
    onFrame: function (cb) { onFrameCb = cb; },
    getMouse: function () { return mouse; },
    getHotspots: function () { return hotspots; },
    isReady: function () { return ready; }
  };
})();
