/* ============================================================
 * 艾瑟兰 · 页面交互
 * 标签页 / 地图控件 / 城市卡片 / 种族图鉴
 * ============================================================ */

(function () {
  'use strict';

  /* ---------------- 启动 3D 世界（最先执行，供后续 UI 绑定） ---------------- */
  World.init();

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

  /* ---------------- 图例（种族分布） ---------------- */

  var legendEl = document.getElementById('legend-list');
  if (legendEl) {
    var html = '';
    for (var k in RACES) {
      var r = RACES[k];
      html +=
        '<button class="legend-item" data-race="' + r.id + '">' +
        '<span class="legend-dot" style="background:' + r.color + ';box-shadow:0 0 8px ' + r.color + '"></span>' +
        '<span class="legend-name">' + r.name + '</span>' +
        '<span class="legend-nation">' + r.nation + '</span>' +
        '</button>';
    }
    legendEl.innerHTML = html;
    var items = legendEl.querySelectorAll('.legend-item');
    for (var li = 0; li < items.length; li++) {
      (function (btn) {
        btn.addEventListener('click', function () {
          var region = null;
          for (var i = 0; i < REGIONS.length; i++) {
            if (REGIONS[i].id === btn.getAttribute('data-race')) { region = REGIONS[i]; break; }
          }
          if (region) World.flyToRegion(region);
        });
      })(items[li]);
    }
  }

  /* ---------------- 地点速览 ---------------- */

  var placeEl = document.getElementById('place-list');
  if (placeEl) {
    var ph = '';
    for (var ci = 0; ci < CITIES.length; ci++) {
      var c = CITIES[ci];
      var race = c.race === 'rift' ? { name: '圣所', color: '#7fe8ff' } : RACES[c.race];
      ph +=
        '<button class="place-item" data-city="' + c.id + '">' +
        '<span class="place-dot" style="background:' + race.color + '"></span>' +
        '<span class="place-name">' + c.name + '</span>' +
        '</button>';
    }
    placeEl.innerHTML = ph;
    var pitems = placeEl.querySelectorAll('.place-item');
    for (var pi = 0; pi < pitems.length; pi++) {
      (function (btn) {
        btn.addEventListener('click', function () {
          var city = null;
          for (var i = 0; i < CITIES.length; i++) {
            if (CITIES[i].id === btn.getAttribute('data-city')) { city = CITIES[i]; break; }
          }
          if (city) World.flyToCity(city);
        });
      })(pitems[pi]);
    }
  }

  /* ---------------- 城市悬停 / 点击 ---------------- */

  var tooltip = document.getElementById('city-tooltip');
  var tipName = document.getElementById('tip-name');
  var tipSub = document.getElementById('tip-sub');

  World.onHover(function (city) {
    if (city && tooltip) {
      var race = city.race === 'rift' ? { name: '星辉裂隙', color: '#7fe8ff' } : RACES[city.race];
      tipName.textContent = city.name;
      tipSub.textContent = race.name + ' · ' + city.title;
      tipSub.style.color = race.color;
      tooltip.classList.add('show');
    } else if (tooltip) {
      tooltip.classList.remove('show');
    }
  });

  var card = document.getElementById('city-card');
  function openCard(city) {
    if (!city || !card) return;
    var race = city.race === 'rift' ? { name: '星辉裂隙', color: '#7fe8ff', id: 'rift' } : RACES[city.race];
    document.getElementById('cc-race-chip').textContent = race.name;
    document.getElementById('cc-race-chip').style.background = race.color;
    document.getElementById('cc-name').textContent = city.name;
    document.getElementById('cc-title').textContent = city.title;
    document.getElementById('cc-pop').textContent = city.pop;
    document.getElementById('cc-ruler').textContent = city.ruler;
    document.getElementById('cc-lore').textContent = city.lore;
    card.classList.add('open');
  }
  function closeCard() { if (card) card.classList.remove('open'); }

  World.onPick(function (city) {
    if (city) openCard(city); else closeCard();
  });
  var cardClose = document.getElementById('cc-close');
  if (cardClose) cardClose.addEventListener('click', closeCard);

  // 卡片跟随鼠标位置（tooltip）
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
      var rc = RACES[a.race];
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
    for (var gi = 0; gi < GLOSSARY.length; gi++) {
      gh2 += '<tr><td class="g-term">' + GLOSSARY[gi][0] + '</td><td>' + GLOSSARY[gi][1] + '</td></tr>';
    }
    gh2 += '</tbody></table>';
    glossEl.innerHTML = gh2;
  }

  // 世界观头部
  document.getElementById('lore-name').textContent = WORLD.name;
  document.getElementById('lore-en').textContent = WORLD.en + ' · THE STARFALL CONTINENT';
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
