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

  var CLICK_KEYS = [
    'gate_dawn', 'gate_speak', 'gate_forge', 'gate_tide',
    'cloister_dawn', 'cloister_speak', 'cloister_forge', 'cloister_tide',
    'library', 'tower', 'observatory', 'pool', 'plaza', 'dorms', 'dorm',
    'forge', 'boat', 'dock', 'ladder',
    'Click_Tower', 'Click_Dawn', 'Click_Speak', 'Click_Forge', 'Click_Tide',
    'Click_Library', 'Click_Pool', 'Click_Yard', 'Click_Prow', 'Click_Dorms'
  ];
  var CLICK_ALIAS = {
    cloister_dawn: 'gate_dawn', cloister_speak: 'gate_speak',
    cloister_forge: 'gate_forge', cloister_tide: 'gate_tide',
    dorm: 'dorms', dock: 'boat',
    Click_Tower: 'tower', Click_Dawn: 'gate_dawn', Click_Speak: 'gate_speak',
    Click_Forge: 'gate_forge', Click_Tide: 'gate_tide', Click_Library: 'library',
    Click_Pool: 'pool', Click_Yard: 'plaza', Click_Prow: 'boat', Click_Dorms: 'dorms'
  };

  function findClick(obj) {
    while (obj) {
      var n = (obj.name || '').split('.')[0];
      for (var i = 0; i < CLICK_KEYS.length; i++) {
        var k = CLICK_KEYS[i];
        if (n === k || n.indexOf(k) === 0) return CLICK_ALIAS[k] || k;
      }
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
    hemi = new THREE.HemisphereLight(0x3a4a6a, 0x1a1520, 0.7);
    scene.add(hemi);
    key = new THREE.DirectionalLight(0x8fa8d8, 1.05);
    key.position.set(-280, 420, -160);
    scene.add(key);
    fill = new THREE.PointLight(0xffb45e, 2.0, 520);
    fill.position.set(0, 250, 0);
    scene.add(fill);
    rim = new THREE.PointLight(0x4fc0ff, 1.8, 900);
    rim.position.set(0, 40, 0);
    scene.add(rim);
  }

  function buildStage() {
    var g = new THREE.CircleGeometry(2200, 48);
    g.rotateX(-Math.PI / 2);
    var sea = new THREE.Mesh(g, new THREE.MeshStandardMaterial({
      color: C(0x071828), roughness: 0.4, metalness: 0.05,
      emissive: C(0x031018), emissiveIntensity: 0.4
    }));
    sea.position.y = -8;
    sea.receiveShadow = true;
    scene.add(sea);

    var beam = new THREE.Mesh(
      new THREE.CylinderGeometry(8, 22, 280, 16, 1, true),
      new THREE.MeshBasicMaterial({
        color: C(0x8fe8ff), transparent: true, opacity: 0.07,
        blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
      })
    );
    beam.position.y = 80;
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
    scene.background = new THREE.Color(0x060a16);
    scene.fog = new THREE.Fog(0x060a16, 900, 2800);

    camera = new THREE.PerspectiveCamera(45, 1, 0.8, 8000);
    camera.position.set(380, 310, 460);

    controls = new THREE.OrbitControls(camera, canvas);
    controls.target.set(0, 220, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 80;
    controls.maxDistance = 1600;
    controls.maxPolarAngle = 1.42;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.28;

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
      scene.background.set(v ? 0x05070e : 0x87a0b8);
      scene.fog.color.set(v ? 0x05070e : 0x87a0b8);
      scene.fog.near = v ? 900 : 1400;
      scene.fog.far = v ? 2800 : 4200;
      if (hemi) hemi.intensity = v ? 0.7 : 1.0;
      if (key) { key.intensity = v ? 1.05 : 1.3; key.color.set(v ? 0x8fa8d8 : 0xffe1b0); }
      if (fill) fill.intensity = v ? 2.0 : 1.1;
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
      camera.position.copy(p.clone().add(dir.multiplyScalar(90)));
      camera.position.y = Math.max(camera.position.y, p.y + 24);
    },
    onPick: function (cb) { onPick = cb; },
    isReady: function () { return ready; }
  };
})();
