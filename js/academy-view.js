/* 星槎学院手册 · 3D 查看器 + 设定渲染（v5）
 * 依赖：vendor/three.min.js(r128) + OrbitControls + GLTFLoader；js/data.js
 * GLB 加载失败 → 自动切平面版学院图（#map-grid）
 */
(function () {
  'use strict';

  var $ = function (s) { return document.querySelector(s); };
  var $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };

  /* ---------------- Tab 切换 ---------------- */
  $('#tabs').addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b) return;
    $$('#tabs button').forEach(function (x) { x.classList.remove('on'); });
    b.classList.add('on');
    $$('.tab').forEach(function (x) { x.classList.remove('on'); });
    $('#tab-' + b.dataset.tab).classList.add('on');
    if (b.dataset.tab === 'island' && viewer) { viewer.resize(); }
  });

  /* ---------------- 文字内容渲染 ---------------- */
  function renderText() {
    // 四院
    $('#houses').innerHTML = HOUSES.map(function (h) {
      return '<article class="house" style="--hc:' + h.color + '">' +
        '<header><span class="mark">' + h.mark + '</span><div>' +
        '<h3>' + h.name + '</h3><p class="answer">光，用来——<b>' + h.answer + '</b></p></div></header>' +
        '<p class="motto">“' + h.motto + '”</p>' +
        '<p class="role">' + h.role + '</p>' +
        '<p class="lore">' + h.lore + '</p>' +
        '<p class="dean">' + h.dean + '</p></article>';
    }).join('');
    // 十谜
    $('#mysteries').innerHTML = MYSTERIES.map(function (m) {
      return '<article class="mystery"><h3><span class="num">#' + m.n + '</span>' + m.t + '</h3>' +
        '<p class="q">' + m.q + '</p><p class="d">' + m.d + '</p></article>';
    }).join('');
    // 岛规
    $('#rules-list').innerHTML = RULES.map(function (r, i) {
      return '<li><span class="rn">' + (i + 1) + '</span>' + r + '</li>';
    }).join('');
    // 人物
    $('#people').innerHTML = PEOPLE.map(function (p) {
      return '<article class="person"><h4>' + p.n + '<span>' + p.r + '</span></h4><p>' + p.d + '</p></article>';
    }).join('');
    // 种族
    $('#races').innerHTML = RACES.map(function (r) {
      return '<article class="race"><h4>' + r.name + '<span>' + r.nation + '</span></h4>' +
        '<p class="motto">“' + r.motto + '”</p><p>' + r.lore + '</p>' +
        '<p class="rels">' + r.rels.map(function (x) { return x[0] + '：' + x[1]; }).join(' · ') + '</p></article>';
    }).join('');
    // 新闻
    $('#news').innerHTML = NEWS412.map(function (n) {
      return '<div class="item"><b>' + n[0] + '</b><p>' + n[1] + '</p></div>';
    }).join('');
    // 名单（左侧）
    $('#ledger-list').innerHTML = NEWS412.slice(0, 5).map(function (n) {
      return '<li><b>' + n[0] + '</b> ' + n[1].slice(0, 42) + '…</li>';
    }).join('');
  }
  renderText();

  /* ---------------- 平面版学院图（fallback + 缩略导航） ---------------- */
  function renderMapGrid() {
    var g = $('#map-grid');
    var angle = function (x, y) { return Math.atan2(x, -y); }; // 北 = -Y 上
    var sorted = BUILDINGS.slice().sort(function (a, b) { return angle(a.pos[0], a.pos[1]) - angle(b.pos[0], b.pos[1]); });
    g.innerHTML = sorted.map(function (b) {
      var r = Math.hypot(b.pos[0], b.pos[1]) / 34 * 44 + 8;   // 0..30 → 8..52%
      var a = angle(b.pos[0], b.pos[1]);
      var x = 50 + Math.sin(a) * r, y = 50 - Math.cos(a) * r;
      return '<button class="dot" data-bid="' + b.id + '" style="left:' + x + '%;top:' + y + '%;--c:' + b.color + '">' +
        '<span class="t">' + b.icon + '</span><span class="name">' + b.name + '</span></button>';
    }).join('');
  }
  function bindMapClicks() {
    var g = $('#map-grid');
    g.addEventListener('click', function (e) {
      var b = e.target.closest('.dot');
      if (!b) return;
      var bd = BUILDINGS.find(function (x) { return x.id === b.dataset.bid; });
      showPopup(bd);
    });
  }

  /* ---------------- 弹窗 ---------------- */
  function showPopup(bd) {
    if (!bd) return;
    $('#popup-body').innerHTML =
      '<h3>' + bd.name + '</h3>' +
      '<p class="tag">' + bd.desc + '</p>' +
      '<p class="lore">' + bd.lore + '</p>' +
      (bd.secret !== '空' && bd.secret ? '<p class="secret">衙门身份 · ' + bd.secret + '</p>' : '');
    $('#popup').classList.remove('hidden');
  }
  $('#popup-close').addEventListener('click', function () { $('#popup').classList.add('hidden'); });
  $('#popup').addEventListener('click', function (e) { if (e.target === this) this.classList.add('hidden'); });

  /* ---------------- 3D 查看器 ---------------- */
  var viewer = null;
  var ATMOS = {
    dusk:  { bg: 0x2a1c12, amb: 0x8a7a66, ambI: 0.9, hemi: 0x807060, dir: 0xffb060, dirI: 1.05 },
    dawn:  { bg: 0x35404e, amb: 0xb0a890, ambI: 1.0, hemi: 0x90a0b0, dir: 0xffd090, dirI: 1.15 },
    night: { bg: 0x0a0e18, amb: 0x2a3550, ambI: 0.55, hemi: 0x40506a, dir: 0x90a0ff, dirI: 0.5 }
  };

  function initViewer() {
    if (typeof THREE === 'undefined' || !$('#stage')) return;
    var stage = $('#stage');
    var renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch (e) { showFallback(); return; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    stage.appendChild(renderer.domElement);

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(42, 2, 0.1, 2000);
    camera.position.set(50, 40, 56);

    var amb = new THREE.AmbientLight(0xffffff, 0.9); scene.add(amb);
    var hemi = new THREE.HemisphereLight(0x807060, 0x3a3228, 0.5); scene.add(hemi);
    var dir = new THREE.DirectionalLight(0xffb060, 1.05); dir.position.set(-40, 50, 30); scene.add(dir);
    var dir2 = new THREE.DirectionalLight(0xa0b0ff, 0.3); dir2.position.set(30, 30, -40); scene.add(dir2);

    var controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; controls.dampingFactor = 0.08;
    controls.maxPolarAngle = Math.PI * 0.55;
    controls.minDistance = 8; controls.maxDistance = 260;
    controls.target.set(0, 4, 0);

    var holo = new THREE.Group(); scene.add(holo);

    var glowGroup = null;
    var loader = new THREE.GLTFLoader();
    loader.load('models/academy.glb', function (gltf) {
      var root = gltf.scene;
      root.traverse(function (o) { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; } });
      holo.add(root);
      $('#stage-fallback').classList.add('hidden');
      buildOverlays(holo, camera, renderer);
    }, undefined, function (err) {
      console.warn('GLB 加载失败，回退平面版', err);
      showFallback();
    });

    function buildOverlays(group, cam) {
      var overlay = document.createElement('div');
      overlay.className = 'dots';
      stage.appendChild(overlay);
      var dots = BUILDINGS.map(function (b) {
        var d = document.createElement('button');
        d.className = 'dot3d'; d.dataset.bid = b.id;
        d.innerHTML = '<span class="t">' + b.icon + '</span><span class="name">' + b.name + '</span>';
        d.style.setProperty('--c', b.color);
        d.addEventListener('click', function () { showPopup(b); });
        overlay.appendChild(d);
        return { b: b, el: d };
      });
      var v = new THREE.Vector3();
      function update() {
        dots.forEach(function (x) {
          v.set(x.b.pos[0], x.b.pos[2] || 2, -x.b.pos[1]);   // Blender Y→three -Z
          v.project(cam);
          if (v.z > 1) { x.el.style.display = 'none'; return; }
          var sx = (v.x * 0.5 + 0.5) * overlay.clientWidth;
          var sy = (-v.y * 0.5 + 0.5) * overlay.clientHeight;
          x.el.style.display = $('#chk-labels').checked ? '' : 'none';
          x.el.style.left = sx + 'px'; x.el.style.top = sy + 'px';
        });
      }
      viewer.overlayTick = update;
    }

    viewer = {
      renderer: renderer, scene: scene, camera: camera,
      overlayTick: null,
      resize: function () {
        var w = stage.clientWidth, h = stage.clientHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h; camera.updateProjectionMatrix();
      },
      setAtmos: function (key) {
        var a = ATMOS[key] || ATMOS.dusk;
        scene.background = new THREE.Color(a.bg);
        amb.color.setHex(a.amb); amb.intensity = a.ambI;
        hemi.color.setHex(a.hemi);
        dir.color.setHex(a.dir); dir.intensity = a.dirI;
      }
    };
    viewer.resize();
    viewer.setAtmos('dusk');

    // 氛围切换
    $('#holo-bar').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-atmos]');
      if (!b || !viewer) return;
      $$('#holo-bar button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      viewer.setAtmos(b.dataset.atmos);
    });

    (function loop() {
      requestAnimationFrame(loop);
      if (!viewer) return;
      controls.update();
      if (viewer.overlayTick) viewer.overlayTick();
      renderer.render(scene, camera);
    })();
    window.addEventListener('resize', function () { if (viewer) viewer.resize(); });
  }

  function showFallback() {
    $('#stage').style.display = 'none';
    $('#stage-fallback').classList.remove('hidden');
    renderMapGrid();
    bindMapClicks();
  }

  /* 启动 */
  initViewer();
  // 若 three 不可用，也先渲染平面图备选
  if (typeof THREE === 'undefined') { renderMapGrid(); bindMapClicks(); $('#stage').style.display = 'none'; $('#stage-fallback').classList.remove('hidden'); }
})();
