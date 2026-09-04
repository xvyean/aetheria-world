/* ============================================================
 * 星槎学院 · 独立 3D 视口
 * 加载 Blender 导出的 academy.glb，点击建筑看志
 * ============================================================ */
var AcademyView = (function () {
  'use strict';

  var canvas, renderer, scene, camera, controls, root;
  var clock = new THREE.Clock();
  var raycaster = new THREE.Raycaster();
  var mouse = new THREE.Vector2();
  var hovered = null;
  var onPick = null;
  var ready = false;
  var night = 0;
  var hemi, key, fill, rim;
  var W = 1, H = 1;
  var bobY = 0;

  function C(h) { return new THREE.Color(h); }

  function findClick(obj) {
    while (obj) {
      if (obj.name && obj.name.indexOf('Click_') === 0) return obj.name;
      obj = obj.parent;
    }
    return null;
  }

  function buildingOf(clickName) {
    if (!window.ACADEMY || !ACADEMY.buildings) return null;
    for (var i = 0; i < ACADEMY.buildings.length; i++) {
      if (ACADEMY.buildings[i].id === clickName) return ACADEMY.buildings[i];
    }
    return null;
  }

  function resize() {
    if (!canvas) return;
    var p = canvas.parentElement;
    if (!p) return;
    W = p.clientWidth; H = p.clientHeight;
    if (W < 2 || H < 2) return;
    renderer.setSize(W, H, false);
    camera.aspect = W / H;
    camera.updateProjectionMatrix();
  }

  function lights() {
    hemi = new THREE.HemisphereLight(0xc9d6e8, 0x3a3228, 0.55);
    scene.add(hemi);
    key = new THREE.DirectionalLight(0xffe1b0, 1.15);
    key.position.set(60, 80, 40);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.left = -70;
    key.shadow.camera.right = 70;
    key.shadow.camera.top = 70;
    key.shadow.camera.bottom = -70;
    key.shadow.bias = -0.0003;
    scene.add(key);
    fill = new THREE.DirectionalLight(0x7eb8d8, 0.35);
    fill.position.set(-50, 30, -20);
    scene.add(fill);
    rim = new THREE.PointLight(0x7fe8ff, 1.4, 160);
    rim.position.set(0, 48, 0);
    scene.add(rim);
  }

  function buildStage() {
    var g = new THREE.CircleGeometry(220, 48);
    g.rotateX(-Math.PI / 2);
    var sea = new THREE.Mesh(g, new THREE.MeshStandardMaterial({
      color: C(0x0d3a52), roughness: 0.35, metalness: 0.05,
      emissive: C(0x042030), emissiveIntensity: 0.25
    }));
    sea.position.y = -36;
    sea.receiveShadow = true;
    scene.add(sea);

    var beam = new THREE.Mesh(
      new THREE.CylinderGeometry(2.2, 5.5, 90, 16, 1, true),
      new THREE.MeshBasicMaterial({
        color: C(0x8fe8ff), transparent: true, opacity: 0.08,
        blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
      })
    );
    beam.position.y = -10;
    scene.add(beam);
  }

  function loadModel() {
    var loader = new THREE.GLTFLoader();
    loader.load('models/academy.glb', function (gltf) {
      root = gltf.scene;
      root.position.set(0, 0, 0);
      root.traverse(function (o) {
        if (o.isMesh) {
          o.castShadow = true;
          o.receiveShadow = true;
          if (o.material) {
            o.material.side = THREE.FrontSide;
            if (o.material.emissive && o.material.emissive.getHex() > 0) {
              o.material.emissiveIntensity = Math.max(o.material.emissiveIntensity || 1, 1.2);
            }
          }
        }
      });
      scene.add(root);
      ready = true;
      var tip = document.getElementById('ac-status');
      if (tip) tip.textContent = '点击一座建筑 · 拖拽旋转 · 滚轮推进';
    }, undefined, function (err) {
      console.error('academy.glb', err);
      var tip = document.getElementById('ac-status');
      if (tip) tip.textContent = '模型未能载入。打开本地服务器后再试。';
    });
  }

  function animate() {
    requestAnimationFrame(animate);
    if (!renderer) return;
    var t = clock.getElapsedTime();
    if (root) {
      root.position.y = Math.sin(t * 0.35) * 0.55;
      bobY = root.position.y;
    }
    if (rim) rim.intensity = 1.2 + Math.sin(t * 1.4) * 0.35 + night * 1.2;
    if (controls) controls.update();
    renderer.render(scene, camera);
  }

  function pick(clientX, clientY) {
    if (!root) return null;
    var rect = canvas.getBoundingClientRect();
    mouse.x = ((clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    var hits = raycaster.intersectObject(root, true);
    if (!hits.length) return null;
    return findClick(hits[0].object);
  }

  function init() {
    canvas = document.getElementById('academy-canvas');
    if (!canvas || typeof THREE === 'undefined' || !THREE.GLTFLoader) return;

    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b1220);
    scene.fog = new THREE.Fog(0x0b1220, 80, 280);

    camera = new THREE.PerspectiveCamera(42, 1, 0.4, 800);
    camera.position.set(72, 38, -58);

    controls = new THREE.OrbitControls(camera, canvas);
    controls.target.set(0, 12, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 28;
    controls.maxDistance = 160;
    controls.maxPolarAngle = 1.35;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.35;

    lights();
    buildStage();
    loadModel();
    resize();
    window.addEventListener('resize', resize);

    var down = null;
    canvas.addEventListener('pointerdown', function (e) {
      down = [e.clientX, e.clientY];
    });
    canvas.addEventListener('click', function (e) {
      if (!down) return;
      var dx = e.clientX - down[0], dy = e.clientY - down[1];
      down = null;
      if (dx * dx + dy * dy > 36) return;
      var id = pick(e.clientX, e.clientY);
      var b = id ? buildingOf(id) : null;
      if (onPick) onPick(b, id);
    });
    canvas.addEventListener('pointermove', function (e) {
      var id = pick(e.clientX, e.clientY);
      canvas.style.cursor = id ? 'pointer' : 'grab';
      if (id !== hovered) {
        hovered = id;
        var tip = document.getElementById('ac-hover');
        if (tip) {
          var b = id ? buildingOf(id) : null;
          tip.textContent = b ? b.name : '';
          tip.classList.toggle('show', !!b);
        }
      }
    });

    animate();
  }

  return {
    init: init,
    resize: resize,
    setNight: function (v) {
      night = v ? 1 : 0;
      if (!scene) return;
      scene.background.set(v ? 0x070b16 : 0x0b1220);
      scene.fog.color.set(v ? 0x070b16 : 0x0b1220);
      if (hemi) hemi.intensity = v ? 0.22 : 0.55;
      if (key) key.intensity = v ? 0.25 : 1.15;
      if (fill) fill.intensity = v ? 0.15 : 0.35;
    },
    flyTo: function (clickName) {
      if (!root || !controls) return;
      var obj = null;
      root.traverse(function (o) { if (o.name === clickName) obj = o; });
      if (!obj) return;
      var p = new THREE.Vector3();
      obj.getWorldPosition(p);
      controls.target.copy(p);
      var dir = camera.position.clone().sub(controls.target).normalize();
      camera.position.copy(p.clone().add(dir.multiplyScalar(36)));
      camera.position.y = Math.max(camera.position.y, p.y + 10);
    },
    onPick: function (cb) { onPick = cb; },
    isReady: function () { return ready; }
  };
})();
