/* ============================================================
 * 星槎学院 GLB 三维查看器
 * three.js r128 (UMD) + GLTFLoader + OrbitControls
 * ============================================================ */
(function () {
  if (typeof THREE === 'undefined') return;

  var canvas = document.getElementById('viewer-canvas');
  if (!canvas) return;

  function resize() {
    var w = canvas.parentElement.clientWidth;
    var h = Math.max(360, w * 0.52);
    canvas.width = w * (window.devicePixelRatio || 1);
    canvas.height = h * (window.devicePixelRatio || 1);
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  var scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x16233f, 220, 420);

  var camera = new THREE.PerspectiveCamera(42, 1.6, 0.1, 1200);
  camera.position.set(56, -62, 46);

  var controls = new THREE.OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.autoRotate = false;
  controls.target.set(0, 0, -2);
  controls.minDistance = 14;
  controls.maxDistance = 170;
  controls.maxPolarAngle = Math.PI * 0.86;

  /* ---- 天空盒（渐变） ---- */
  var skyGeo = new THREE.SphereGeometry(560, 24, 16);
  var skyMat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: {
      top: { value: new THREE.Color(0x0f1e3c) },
      mid: { value: new THREE.Color(0x2b4a86) },
      bot: { value: new THREE.Color(0xf2b665) }
    },
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader: [
      'varying vec3 vP; uniform vec3 top; uniform vec3 mid; uniform vec3 bot;',
      'void main(){ float h = normalize(vP).y;',
      ' vec3 c = h > 0.0 ? mix(mid, top, clamp(h*1.6,0.,1.)) : mix(mid, bot, clamp(-h*2.2,0.,1.));',
      ' gl_FragColor = vec4(c, 1.0); }'
    ].join('\n')
  });
  scene.add(new THREE.Mesh(skyGeo, skyMat));

  /* ---- 星辉裂隙光柱（底部氛围） ---- */
  var beamMat = new THREE.MeshBasicMaterial({
    color: 0x9fe4ff, transparent: true, opacity: 0.28,
    blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
  });
  var beam = new THREE.Mesh(new THREE.CylinderGeometry(5.2, 9.5, 150, 24, 1, true), beamMat);
  beam.position.y = -92;
  scene.add(beam);
  var glowPts = new THREE.Points(
    (function () {
      var n = 260, pos = new Float32Array(n * 3);
      for (var i = 0; i < n; i++) {
        var a = Math.random() * Math.PI * 2, r = Math.pow(Math.random(), 0.6) * 26;
        pos[i * 3] = Math.cos(a) * r;
        pos[i * 3 + 1] = -90 + Math.random() * 100;
        pos[i * 3 + 2] = Math.sin(a) * r;
      }
      var g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      return g;
    })(),
    new THREE.PointsMaterial({ color: 0xbfefff, size: 0.9, transparent: true, opacity: 0.55,
      blending: THREE.AdditiveBlending, depthWrite: false })
  );
  scene.add(glowPts);

  /* ---- 灯光 ---- */
  scene.add(new THREE.HemisphereLight(0x8fb2ff, 0x2a2438, 0.55));
  var sun = new THREE.DirectionalLight(0xffc98a, 1.5);
  sun.position.set(-80, 60, -50);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.near = 20; sun.shadow.camera.far = 300;
  sun.shadow.camera.left = -70; sun.shadow.camera.right = 70;
  sun.shadow.camera.top = 70; sun.shadow.camera.bottom = -70;
  scene.add(sun);
  var fill = new THREE.DirectionalLight(0x5f7fd0, 0.35);
  fill.position.set(60, 40, 60);
  scene.add(fill);
  var crystalLight = new THREE.PointLight(0xbfefff, 2.2, 90, 1.6);
  crystalLight.position.set(0, 40, 0);
  scene.add(crystalLight);

  /* ---- 学院模型 ---- */
  var academy = null;
  var loader = new THREE.GLTFLoader();
  loader.load('models/academy.glb', function (gltf) {
    academy = gltf.scene;
    academy.traverse(function (o) {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
        if (o.material) {
          o.material.side = THREE.FrontSide;
          if (o.material.emissive && o.material.emissiveIntensity === undefined) {
            o.material.emissiveIntensity = 1.0;
          }
        }
      }
    });
    scene.add(academy);
    var hint = document.querySelector('.viewer-hud');
    if (hint) hint.classList.add('loaded');
  }, undefined, function (err) {
    console.warn('GLB 加载失败（请通过本地服务器打开，或检查 models/academy.glb 是否存在于同目录）', err);
    var hint = document.querySelector('.viewer-hud');
    if (hint) hint.textContent = '⚠ 请通过本地服务器访问（如 python3 -m http.server）以加载 GLB';
  });

  /* ---- 交互 ---- */
  var raycaster = new THREE.Raycaster();
  var downPos = null;
  canvas.addEventListener('pointerdown', function (e) { downPos = [e.clientX, e.clientY]; });
  canvas.addEventListener('pointerup', function (e) {
    if (!downPos) return;
    var dx = e.clientX - downPos[0], dy = e.clientY - downPos[1];
    if (dx * dx + dy * dy > 16) return;
    var rect = canvas.getBoundingClientRect();
    var m = new THREE.Vector2(((e.clientX - rect.left) / rect.width) * 2 - 1,
                              -((e.clientY - rect.top) / rect.height) * 2 + 1);
    raycaster.setFromCamera(m, camera);
    if (academy) {
      var hits = raycaster.intersectObject(academy, true);
      if (hits.length) {
        var p = hits[0].point;
        controls.target.copy(p);
      }
    }
  });
  canvas.addEventListener('dblclick', function () {
    controls.target.set(0, 0, -2);
    camera.position.set(56, -62, 46);
  });

  window.addEventListener('resize', resize);
  resize();

  var t = 0;
  (function loop() {
    requestAnimationFrame(loop);
    t += 0.008;
    if (academy) {
      academy.position.y = Math.sin(t * 1.2) * 0.7 + 0.9;   // 潮汐呼吸
      academy.rotation.y = Math.sin(t * 0.3) * 0.06;
    }
    beam.rotation.y = t * 0.35;
    glowPts.position.y = Math.sin(t * 0.5) * 1.2;
    crystalLight.intensity = 2.2 + Math.sin(t * 2.0) * 0.5;
    controls.update();
    renderer.render(scene, camera);
  })();
})();
