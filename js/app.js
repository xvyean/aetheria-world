/* ============================================================
 * 艾瑟兰 · 页面交互 v2
 * 标签页 / 十四势力图例 / 城市卡片 / 种族图鉴 / 地理志
 * ============================================================ */

(function () {
  'use strict';

  /* ---------------- 启动 3D 世界（最先执行，供后续 UI 绑定） ---------------- */
  World.init();

  function factionById(id) {
    for (var i = 0; i < FACTIONS.length; i++) {
      if (FACTIONS[i].id === id) return FACTIONS[i];
    }
    return FACTIONS[0];
  }

  /* ---------------- 标签页 ---------------- */

  var tabs = document.querySelectorAll('.tab');
  var panes = document.querySelectorAll('.tabpane');

  function switchTab(id) {
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].classList.toggle('active', tabs[i].getAttribute('data-tab') === id);
    }
    for (var j = 0; j < panes.length; j++) {
      panes[j].classList.toggle('active', panes[j].id === 'tab-' + id);
    }
    if (id === 'map') {
      requestAnimationFrame(function () { World.resize(); });
    }
  }

  for (var ti = 0; ti < tabs.length; ti++) {
    (function (btn) {
      btn.addEventListener('click', function () {
        switchTab(btn.getAttribute('data-tab'));
      });
    })(tabs[ti]);
  }

  /* ---------------- 图例（十四势力） ---------------- */

  var legendEl = document.getElementById('legend-list');
  if (legendEl) {
    var html = '';
    for (var k = 0; k < FACTIONS.length; k++) {
      var f = FACTIONS[k];
      html +=
        '<button class="legend-item" data-faction="' + f.id + '">' +
        '<span class="legend-dot" style="background:' + f.color + ';box-shadow:0 0 8px ' + f.color + '"></span>' +
        '<span class="legend-name">' + f.name + '</span>' +
        '<span class="legend-nation">' + f.kind + '</span>' +
        '</button>';
    }
    legendEl.innerHTML = html;
    var items = legendEl.querySelectorAll('.legend-item');
    for (var li = 0; li < items.length; li++) {
      (function (btn) {
        btn.addEventListener('click', function () {
          World.flyToFaction(factionById(btn.getAttribute('data-faction')));
        });
      })(items[li]);
    }
  }

  /* ---------------- 地点速览（十四都 + 星槎 / 城 · 镇 · 村） ---------------- */

  var capEl = document.getElementById('place-caps');
  var placeEl = document.getElementById('place-list');
  if (capEl && placeEl) {
    var ch = '';
    for (var ci = 0; ci < CITIES.length; ci++) {
      var c = CITIES[ci];
      if ((c.tier || 'capital') !== 'capital') continue;
      var f = factionById(c.faction);
      ch +=
        '<button class="place-item place-cap" data-city="' + c.id + '">' +
        '<span class="place-dot" style="background:' + f.color + ';box-shadow:0 0 7px ' + f.color + '"></span>' +
        '<span class="place-name">' + c.name + '</span>' +
        '</button>';
    }
    ch +=
      '<button class="place-item place-cap place-academy" data-city="academy">' +
      '<span class="place-dot" style="background:#f2e8c8;box-shadow:0 0 9px #ffe9a8"></span>' +
      '<span class="place-name">✦ 星槎学院</span>' +
      '</button>';
    capEl.innerHTML = ch;

    var ph = '';
    for (var ci2 = 0; ci2 < CITIES.length; ci2++) {
      var c2 = CITIES[ci2];
      if ((c2.tier || 'capital') === 'capital') continue;
      var f2 = factionById(c2.faction);
      ph +=
        '<button class="place-item place-' + c2.tier + '" data-city="' + c2.id + '">' +
        '<span class="place-dot" style="background:' + f2.color + '"></span>' +
        '<span class="place-name">' + c2.name + '</span>' +
        '</button>';
    }
    placeEl.innerHTML = ph;

    var all = document.querySelectorAll('.place-item');
    for (var pi = 0; pi < all.length; pi++) {
      (function (btn) {
        btn.addEventListener('click', function () {
          var id = btn.getAttribute('data-city');
          if (id === 'academy') { World.flyToAcademy(); return; }
          for (var i2 = 0; i2 < CITIES.length; i2++) {
            if (CITIES[i2].id === id) { World.flyToCity(CITIES[i2]); break; }
          }
        });
      })(all[pi]);
    }
  }

  /* ---------------- 城市悬停 / 点击 ---------------- */

  var tooltip = document.getElementById('city-tooltip');
  var tipName = document.getElementById('tip-name');
  var tipSub = document.getElementById('tip-sub');

  World.onHover(function (city) {
    if (city && tooltip) {
      if (city.id === 'academy') {
        tipName.textContent = city.name;
        tipSub.textContent = '空岛学府 · ' + city.title;
        tipSub.style.color = '#f2e8c8';
      } else {
        var f = factionById(city.faction);
        tipName.textContent = city.name;
        tipSub.textContent = f.name + ' · ' + city.title;
        tipSub.style.color = f.color;
      }
      tooltip.classList.add('show');
    } else if (tooltip) {
      tooltip.classList.remove('show');
    }
  });

  var card = document.getElementById('city-card');
  function openCard(city) {
    if (!city || !card) return;
    if (city.id === 'academy') {
      document.getElementById('cc-race-chip').textContent = '星槎';
      document.getElementById('cc-race-chip').style.background = '#f2e8c8';
      document.getElementById('cc-name').textContent = '星槎学院';
      document.getElementById('cc-title').textContent = ACADEMY.subtitle;
      document.getElementById('cc-pop').textContent = ACADEMY.location;
      document.getElementById('cc-ruler').textContent = ACADEMY.head;
      document.getElementById('cc-lore').textContent =
        ACADEMY.motto + ' 创立：' + ACADEMY.founded + '。' + ACADEMY.admission;
      document.getElementById('cc-goto').style.display = '';
      card.classList.add('open');
      return;
    }
    document.getElementById('cc-goto').style.display = 'none';
    var f = factionById(city.faction);
    var rc = RACES[f.race] || { name: '星辉' };
    var tierName = city.tier === 'city' ? '大城' : (city.tier === 'town' ? '镇' : (city.tier === 'village' ? '村' : '首都'));
    document.getElementById('cc-race-chip').textContent = f.name + ' · ' + tierName;
    document.getElementById('cc-race-chip').style.background = f.color;
    document.getElementById('cc-name').textContent = city.name;
    document.getElementById('cc-title').textContent = city.title;
    document.getElementById('cc-pop').textContent = city.pop;
    document.getElementById('cc-ruler').textContent = city.ruler || f.ruler;
    document.getElementById('cc-lore').textContent = city.lore + '（' + f.name + ' · ' + f.kind + '，' + rc.name + '）';
    card.classList.add('open');
  }
  function closeCard() { if (card) card.classList.remove('open'); }
  document.getElementById('cc-goto').addEventListener('click', function () { closeCard(); switchTab('academy'); });

  World.onPick(function (city) {
    if (city) openCard(city); else closeCard();
  });
  var cardClose = document.getElementById('cc-close');
  if (cardClose) cardClose.addEventListener('click', closeCard);

  var mapPane = document.getElementById('tab-map');
  if (mapPane && tooltip) {
    mapPane.addEventListener('pointermove', function (e) {
      var rect = mapPane.getBoundingClientRect();
      var x = e.clientX - rect.left + 16;
      var y = e.clientY - rect.top + 14;
      if (x + 240 > rect.width) x = e.clientX - rect.left - 250;
      tooltip.style.transform = 'translate(' + x + 'px,' + y + 'px)';
    });
  }

  /* ---------------- 时间 / 视角控件 ---------------- */

  var presetBtns = document.querySelectorAll('.preset-btn');
  function markPreset(name) {
    for (var i = 0; i < presetBtns.length; i++) {
      presetBtns[i].classList.toggle('active', presetBtns[i].getAttribute('data-preset') === name);
    }
  }
  for (var pb = 0; pb < presetBtns.length; pb++) {
    (function (btn) {
      btn.addEventListener('click', function () {
        var name = btn.getAttribute('data-preset');
        World.setPreset(name);
        markPreset(name);
      });
    })(presetBtns[pb]);
  }

  var autoBtn = document.getElementById('btn-auto');
  window.__syncAutoBtn = function (b) {
    if (autoBtn) autoBtn.classList.toggle('active', b);
  };
  if (autoBtn) {
    autoBtn.addEventListener('click', function () {
      var b = !World.getAutoRotate();
      World.setAutoRotate(b);
      autoBtn.classList.toggle('active', b);
    });
    autoBtn.classList.add('active');
    World.setAutoRotate(true);
  }

  var resetBtn = document.getElementById('btn-reset');
  if (resetBtn) resetBtn.addEventListener('click', function () {
    World.resetView();
  });

  /* ---------------- 种族图鉴 ---------------- */

  function bar(label, v) {
    return '<div class="bar-row"><span class="bar-label">' + label + '</span>' +
      '<span class="bar-track"><span class="bar-fill" style="width:' + v + '%"></span></span>' +
      '<span class="bar-val">' + v + '</span></div>';
  }

  var grid = document.getElementById('race-grid');
  if (grid) {
    var gh = '';
    for (var rk in RACES) {
      var r = RACES[rk];
      var rels = '';
      for (var ri = 0; ri < r.rels.length; ri++) {
        var rel = r.rels[ri];
        var tone = rel[1] === '宿敌' || rel[1] === '世仇' || rel[1] === '敌对' || rel[1] === '憎恶'
          ? 'hostile' : (rel[1] === '友善' || rel[1] === '盟友' || rel[1] === '互敬'
          ? 'friend' : 'neutral');
        rels += '<span class="rel-chip ' + tone + '"><b>' + rel[0] + '</b>' + rel[1] + '</span>';
      }
      gh +=
        '<article class="race-card" style="--rc:' + r.color + '">' +
        '<div class="race-head">' +
        '<div class="race-emblem"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">' + r.emblem + '</svg></div>' +
        '<div class="race-titles"><h3>' + r.name + ' · ' + r.nation + '</h3>' +
        '<p class="race-motto">' + r.motto + '</p></div>' +
        '</div>' +
        '<div class="race-meta">' +
        '<div><span>人口</span>' + r.pop + '</div>' +
        '<div><span>寿命</span>' + r.life + '</div>' +
        '<div><span>领地</span>' + r.territory + '</div>' +
        '</div>' +
        '<div class="race-bars">' +
        bar('体魄', r.st['体魄']) + bar('魅力', r.st['魅力']) + bar('智慧', r.st['智慧']) +
        '</div>' +
        '<p class="race-lore">' + r.lore + '</p>' +
        '<div class="race-facts">' +
        '<div><b>文化</b>' + r.culture + '</div>' +
        '<div><b>信仰</b>' + r.faith + '</div>' +
        '<div><b>名士</b>' + r.famous + '</div>' +
        '</div>' +
        '<div class="race-rel">' + rels + '</div>' +
        '</article>';
    }
    grid.innerHTML = gh;
  }

  /* ---------------- 星槎学院：船票 / 志书 ---------------- */

  var A = ACADEMY;
  function setText(id, t) { var el = document.getElementById(id); if (el) el.textContent = t; }
  setText('academy-motto', '“' + A.motto + '”');
  setText('academy-founded', A.founded);
  setText('academy-lifted', A.lifted);
  setText('academy-head', A.head);
  setText('academy-admit', A.admission);
  setText('academy-location', A.location);
  setText('ticket-front', A.ticket.front.replace(/ ／ /g, '\n'));
  setText('ticket-back', A.ticket.back);

  function paras(id, arr) {
    var el = document.getElementById(id);
    if (!el) return;
    var h = '';
    for (var i = 0; i < arr.length; i++) h += '<p' + (i === 0 ? ' class="dropcap"' : '') + '>' + arr[i] + '</p>';
    el.innerHTML = h;
  }
  paras('academy-intro', A.intro);
  paras('academy-history', A.history);

  var houseEl = document.getElementById('house-grid');
  if (houseEl) {
    var imgMap = { dawn: 'house-dawn.jpg', speak: 'house-speak.jpg', forge: 'house-forge.jpg', tide: 'house-tide.jpg' };
    var hh2 = '';
    for (var hj = 0; hj < A.houses.length; hj++) {
      var hs = A.houses[hj];
      var rules = '';
      for (var ri = 0; ri < (hs.rules || []).length; ri++) rules += '<li>' + hs.rules[ri] + '</li>';
      hh2 +=
        '<article class="house-card" style="--hc:' + hs.color + '" data-spot="' + hs.id + '">' +
        '<div class="house-emblem"><img src="img/' + (imgMap[hs.id] || '') + '" alt="' + hs.sigil + '徽记"></div>' +
        '<div class="house-head">' +
        '<h3>' + hs.name + '</h3>' +
        '<p class="house-motto">“' + hs.motto + '”</p>' +
        '</div>' +
        '<div class="house-tags">' +
        '<span>学派 · ' + hs.element + '</span>' +
        '<span>院德 · ' + hs.virtue + '</span>' +
        '<span>徽记 · ' + hs.sigil + '</span>' +
        '</div>' +
        '<p class="house-desc">' + hs.desc + '</p>' +
        '<p class="house-tower">' + hs.tower + '</p>' +
        '<p class="house-head-line">' + hs.head + '</p>' +
        '<ul class="house-rules">' + rules + '</ul>' +
        '<div class="house-foot">' +
        '<div><b>开院</b>' + hs.founded + '</div>' +
        '<div><b>名士</b>' + hs.alumni + '</div>' +
        '</div>' +
        '</article>';
    }
    houseEl.innerHTML = hh2;
  }

  setText('academy-sorting', A.sorting.desc);
  var recEl = document.getElementById('sorting-records');
  if (recEl) {
    var rh0 = '';
    for (var rc = 0; rc < A.sorting.records.length; rc++) rh0 += '<div><b>' + A.sorting.records[rc].year + ' · 分选记录</b>' + A.sorting.records[rc].text + '</div>';
    recEl.innerHTML = rh0;
  }

  var ftEl = document.getElementById('ferry-table');
  if (ftEl) {
    var fh = '';
    for (var fr = 0; fr < A.ferry.rows.length; fr++) fh += '<tr><td>' + A.ferry.rows[fr][0] + '</td><td>' + A.ferry.rows[fr][1] + '</td></tr>';
    ftEl.innerHTML = fh;
  }
  setText('ferry-desc', A.ferry.desc);
  setText('ferry-man', A.ferry.ferryman);

  var lawEl = document.getElementById('academy-laws');
  if (lawEl) {
    var lh = '';
    for (var lw = 0; lw < A.laws.length; lw++) lh += '<li><b>' + A.laws[lw][0] + '</b><span>' + A.laws[lw][1] + '</span></li>';
    lawEl.innerHTML = lh;
  }
  var trEl = document.getElementById('academy-tributes');
  if (trEl) {
    var th = '';
    for (var tb = 0; tb < A.tributes.length; tb++) th += '<div><b>' + A.tributes[tb][0] + '</b><span>' + A.tributes[tb][1] + '</span></div>';
    trEl.innerHTML = th;
  }

  var ritEl = document.getElementById('academy-rituals');
  if (ritEl) {
    var rh = '';
    for (var rti = 0; rti < A.rituals.length; rti++) {
      rh += '<div class="academy-item"><h5>' + A.rituals[rti].name + '</h5><p>' + A.rituals[rti].desc + '</p></div>';
    }
    ritEl.innerHTML = rh;
  }
  var mkEl = document.getElementById('academy-making');
  if (mkEl) {
    mkEl.innerHTML =
      '<p><b>建模</b> 整座空岛用 Blender Python 程序化生成（<code>blender/academy/build.py</code>）：500 × 360 米岛体、中央旧学宫、外城墙、四门、四条大道与七个扩建校区——共约 8,900 个部件、35.7 万顶点。</p>' +
      '<p><b>导出</b> 合并为 454 个网格，顶点色着色（无贴图），Draco 压缩 glTF 约 3.7 MB；可动部件保留 <code>extras</code>（fx 类型、轨道参数、志书键），网页端据此点火、转晶、涨潮、开船。</p>' +
      '<p><b>渲染</b> Cycles + AgX，附带云海与 Mist 大气合成，八个机位的成图在 <code>models/render_*.png</code>。</p>';
  }

  /* ---------------- 星槎学院：三维舞台 ---------------- */

  var SPOT_ORDER = ['city_wall', 'scholar_quarter', 'dawn_quarter', 'forge_quarter', 'tide_quarter', 'residence_quarter', 'service_quarter', 'garden_quarter',
    'star_tower', 'crystal', 'pillars', 'corridors', 'dawn', 'speak', 'sycamore', 'forge', 'old_steps', 'tide', 'pier', 'ferry', 'pool',
    'grain_hall', 'history_hall', 'tide_hall', 'kitchen', 'ember', 'bell', 'dorms', 'paddock', 'root'];
  // 远景只标大地标，近景才显示全部，避免地名挤成一团
  var SPOT_MAJOR = { city_wall: 1, scholar_quarter: 1, dawn_quarter: 1, forge_quarter: 1, tide_quarter: 1,
    residence_quarter: 1, service_quarter: 1, garden_quarter: 1, star_tower: 1, pier: 1, root: 1 };
  var stage = document.getElementById('academy-stage');
  var spotCard = document.getElementById('spot-card');
  var spotList = document.getElementById('spot-list');
  var labelsEl = document.getElementById('academy-labels');
  var hoverEl = document.getElementById('academy-hover');
  var hintEl = document.getElementById('academy-hint');
  var currentSpot = null;
  var labelsOn = true;
  var academyStarted = false;
  var labelNodes = {};

  function spotName(key) { return (A.spots[key] && A.spots[key].name) || key; }

  function showSpot(key, fly) {
    var sp = A.spots[key];
    if (!sp || !spotCard) return;
    currentSpot = key;
    document.getElementById('spot-sub').textContent = sp.sub || '';
    document.getElementById('spot-name').textContent = sp.name;
    document.getElementById('spot-text').textContent = sp.text;
    var idx = SPOT_ORDER.indexOf(key);
    document.getElementById('spot-index').textContent = (idx + 1) + ' / ' + SPOT_ORDER.length;
    spotCard.classList.add('open');
    spotCard.scrollTop = 0;
    if (fly !== false && window.Academy3D) Academy3D.flyToHotspot(key);
    var bts = spotList ? spotList.querySelectorAll('button') : [];
    for (var i = 0; i < bts.length; i++) bts[i].classList.toggle('active', bts[i].getAttribute('data-spot') === key);
    for (var k in labelNodes) labelNodes[k].classList.toggle('hot', k === key);
  }
  function closeSpot() {
    currentSpot = null;
    if (spotCard) spotCard.classList.remove('open');
    var bts = spotList ? spotList.querySelectorAll('button') : [];
    for (var i = 0; i < bts.length; i++) bts[i].classList.remove('active');
    for (var k in labelNodes) labelNodes[k].classList.remove('hot');
  }
  function stepSpot(d) {
    var idx = currentSpot ? SPOT_ORDER.indexOf(currentSpot) : -1;
    idx = (idx + d + SPOT_ORDER.length) % SPOT_ORDER.length;
    showSpot(SPOT_ORDER[idx]);
  }

  if (spotList) {
    var sh = '';
    for (var si = 0; si < SPOT_ORDER.length; si++) sh += '<button data-spot="' + SPOT_ORDER[si] + '">' + spotName(SPOT_ORDER[si]) + '</button>';
    spotList.innerHTML = sh;
    spotList.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-spot]');
      if (!b) return;
      showSpot(b.getAttribute('data-spot'));
      if (stage) stage.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }
  if (houseEl) {
    houseEl.addEventListener('click', function (e) {
      var c = e.target.closest('.house-card');
      if (!c) return;
      showSpot(c.getAttribute('data-spot'));
      if (stage) stage.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }
  document.getElementById('spot-close').addEventListener('click', closeSpot);
  document.getElementById('spot-prev').addEventListener('click', function () { stepSpot(-1); });
  document.getElementById('spot-next').addEventListener('click', function () { stepSpot(1); });

  function startAcademy3D() {
    if (academyStarted || !window.Academy3D || !window.THREE) return;
    academyStarted = true;
    var loadEl = document.getElementById('academy-loading');
    var progEl = document.getElementById('academy-progress');

    // 地名浮标
    if (labelsEl) {
      for (var i = 0; i < SPOT_ORDER.length; i++) {
        var d = document.createElement('div');
        d.className = 'alabel';
        d.innerHTML = '<span>' + spotName(SPOT_ORDER[i]) + '</span><i></i>';
        labelsEl.appendChild(d);
        labelNodes[SPOT_ORDER[i]] = d;
      }
    }

    Academy3D.onProgress(function (f) { if (progEl) progEl.textContent = Math.round(f * 100) + '%'; });
    Academy3D.onReady(function () {
      if (loadEl) loadEl.classList.add('done');
      setTimeout(function () { if (hintEl) hintEl.classList.add('fade'); }, 6000);
    });
    Academy3D.onHover(function (key, h) {
      if (!hoverEl) return;
      if (!key) { hoverEl.classList.remove('on'); return; }
      hoverEl.textContent = spotName(key);
      hoverEl.classList.add('on');
    });
    Academy3D.onPick(function (key) {
      if (key) showSpot(key); else closeSpot();
    });
    var placed = [];
    Academy3D.onFrame(function () {
      if (!labelsOn || !labelsEl) return;
      var pts = Academy3D.projectHotspots();
      // 近的优先摆放；当前选中的最优先；互相重叠的后来者隐藏
      pts.sort(function (a, b) { return (a.key === currentSpot ? -1e9 : a.dist) - (b.key === currentSpot ? -1e9 : b.dist); });
      placed.length = 0;
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i], n = labelNodes[p.key];
        if (!n) continue;
        var vis = p.visible && !p.occluded && p.dist < (SPOT_MAJOR[p.key] ? 300 : 120);
        if (currentSpot === p.key) vis = p.visible;
        if (vis) {
          var w = (n.firstChild.textContent.length * 12.5) + 8, h = 22;
          var x0 = p.x - w / 2, y0 = p.y - 14 - h;
          for (var j = 0; j < placed.length; j++) {
            var r = placed[j];
            if (x0 < r[2] && x0 + w > r[0] && y0 < r[3] && y0 + h > r[1]) { vis = false; break; }
          }
          if (vis) placed.push([x0, y0, x0 + w, y0 + h]);
        }
        n.classList.toggle('vis', vis);
        if (vis) {
          n.style.transform = 'translate(' + p.x + 'px,' + (p.y - 14) + 'px) translate(-50%,-100%)';
          n.classList.toggle('far', p.dist > 150);
        }
      }
      if (hoverEl && hoverEl.classList.contains('on')) {
        var m = Academy3D.getMouse();
        hoverEl.style.left = m.x + 'px'; hoverEl.style.top = m.y + 'px';
      }
    });
    Academy3D.init({ canvasId: 'academy-canvas', model: 'models/xingcha_academy.glb', hotspots: 'models/xingcha_academy.hotspots.json' });

    // 控件
    var pbtns = document.querySelectorAll('#academy-presets .preset-btn');
    for (var pi = 0; pi < pbtns.length; pi++) {
      (function (btn) {
        btn.addEventListener('click', function () {
          for (var j = 0; j < pbtns.length; j++) pbtns[j].classList.toggle('active', pbtns[j] === btn);
          Academy3D.setPreset(btn.getAttribute('data-preset'));
        });
      })(pbtns[pi]);
    }
    document.getElementById('academy-home').addEventListener('click', function () { closeSpot(); Academy3D.flyHome(); });
    document.getElementById('academy-under').addEventListener('click', function () { showSpot('root', false); Academy3D.flyUnder(); });
    var orbitBtn = document.getElementById('academy-orbit');
    orbitBtn.addEventListener('click', function () {
      var on = !Academy3D.getAutoRotate();
      Academy3D.setAutoRotate(on);
      orbitBtn.classList.toggle('active', on);
    });
    var lblBtn = document.getElementById('academy-labels-toggle');
    lblBtn.classList.add('active');
    lblBtn.addEventListener('click', function () {
      labelsOn = !labelsOn;
      lblBtn.classList.toggle('active', labelsOn);
      if (labelsEl) labelsEl.classList.toggle('hidden', !labelsOn);
    });
    document.getElementById('academy-full').addEventListener('click', function () {
      if (!document.fullscreenElement) { if (stage.requestFullscreen) stage.requestFullscreen(); }
      else if (document.exitFullscreen) document.exitFullscreen();
    });
    document.addEventListener('fullscreenchange', function () { requestAnimationFrame(function () { Academy3D.resize(); }); });
    document.addEventListener('keydown', function (e) {
      if (!document.getElementById('tab-academy').classList.contains('active')) return;
      if (e.key === 'Escape') closeSpot();
      else if (e.key === 'ArrowRight' || e.key === ']') stepSpot(1);
      else if (e.key === 'ArrowLeft' || e.key === '[') stepSpot(-1);
    });
  }

  // 只有切到学院页才启动第二个 WebGL 场景；离开时暂停渲染
  var origSwitch = switchTab;
  switchTab = function (id) {
    origSwitch(id);
    if (id === 'academy') {
      startAcademy3D();
      if (window.Academy3D) { Academy3D.setVisible(true); requestAnimationFrame(function () { Academy3D.resize(); }); }
      if (window.World && World.setPaused) World.setPaused(true);
    } else {
      if (window.Academy3D && academyStarted) Academy3D.setVisible(false);
      if (window.World && World.setPaused) World.setPaused(false);
    }
  };
  if (location.hash === '#academy') switchTab('academy');

  /* ---------------- 世界观：动态注入 ---------------- */

  // 纪元年表
  var chronEl = document.getElementById('chronicle-list');
  if (chronEl) {
    var ch = '';
    for (var i2 = 0; i2 < CHRONICLE.length; i2++) {
      var e = CHRONICLE[i2];
      ch +=
        '<div class="chrono-item">' +
        '<div class="chrono-node"><span></span></div>' +
        '<div class="chrono-body">' +
        '<div class="chrono-era">' + e.era + '<span class="chrono-year">' + e.year + '</span></div>' +
        '<h4>' + e.title + '</h4>' +
        '<p>' + e.desc + '</p>' +
        '</div>' +
        '</div>';
    }
    chronEl.innerHTML = ch;
  }

  // 地理志（十景）
  var geoEl = document.getElementById('geo-grid');
  if (geoEl) {
    var ghtml = '';
    for (var gi = 0; gi < GEOGRAPHY.length; gi++) {
      var geo = GEOGRAPHY[gi];
      ghtml +=
        '<div class="geo-card' + (geo.color === '#7fe8ff' ? ' geo-rift' : '') + '" style="--gc:' + geo.color + '">' +
        '<h4>' + geo.name + ' <small>' + geo.who + '</small></h4>' +
        '<p>' + geo.desc + '</p>' +
        '</div>';
    }
    geoEl.innerHTML = ghtml;
  }

  // 魔法学派
  var schoolEl = document.getElementById('school-grid');
  if (schoolEl) {
    var sh = '';
    for (var mi = 0; mi < MAGIC.schools.length; mi++) {
      var s = MAGIC.schools[mi];
      sh +=
        '<div class="school-card" style="--sc:' + s.color + '">' +
        '<div class="school-head"><span class="school-who">' + s.who + '</span><h4>' + s.name + '</h4></div>' +
        '<p>' + s.desc + '</p>' +
        '</div>';
    }
    schoolEl.innerHTML = sh;
    document.getElementById('magic-intro').textContent = MAGIC.intro;
  }

  // 神器
  var artEl = document.getElementById('artifact-list');
  if (artEl) {
    var ah = '';
    for (var ai = 0; ai < ARTIFACTS.length; ai++) {
      var a = ARTIFACTS[ai];
      var rc = RACES[a.race] || { color: '#7fd8e8', nation: '星辉圣地' };
      ah +=
        '<div class="artifact-row">' +
        '<span class="artifact-name"><i style="background:' + rc.color + '"></i>' + a.name + '</span>' +
        '<span class="artifact-race">' + rc.nation + '</span>' +
        '<p>' + a.desc + '</p>' +
        '</div>';
    }
    artEl.innerHTML = ah;
  }

  // 名词典
  var glossEl = document.getElementById('glossary-table');
  if (glossEl) {
    var gh2 = '<table><thead><tr><th>词条</th><th>释义</th></tr></thead><tbody>';
    for (var gi2 = 0; gi2 < GLOSSARY.length; gi2++) {
      gh2 += '<tr><td class="g-term">' + GLOSSARY[gi2][0] + '</td><td>' + GLOSSARY[gi2][1] + '</td></tr>';
    }
    gh2 += '</tbody></table>';
    glossEl.innerHTML = gh2;
  }

  // 世界观头部
  document.getElementById('lore-name').textContent = WORLD.name;
  document.getElementById('lore-en').textContent = WORLD.en + ' · THREE CONTINENTS, ONE FLOATING ISLE';
  document.getElementById('lore-epigraph').textContent = WORLD.epigraph;
  document.getElementById('lore-epigraph-source').textContent = WORLD.epigraphSource;
  document.getElementById('lore-year').textContent = WORLD.year;
  document.getElementById('map-year').textContent = WORLD.year + ' · ' + WORLD.tagline;

  /* ---------------- 加载幕布 ---------------- */

  var loading = document.getElementById('loading');

  window.addEventListener('load', function () {
    setTimeout(function () {
      if (loading) {
        loading.classList.add('done');
        setTimeout(function () {
          if (loading) loading.style.display = 'none';
        }, 1200);
      }
    }, 1500);
  });
})();
