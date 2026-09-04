/* ============================================================
 * 艾瑟兰 · 页面交互 v2
 * 标签页 / 十四势力图例 / 城市卡片 / 种族图鉴 / 地理志
 * ============================================================ */

(function () {
  'use strict';

  /* ---------------- 启动 3D 世界（最先执行，供后续 UI 绑定） ---------------- */
  World.init();
  if (window.AcademyView) AcademyView.init();


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
    if (id === 'academy' && window.AcademyView) {
      requestAnimationFrame(function () { AcademyView.resize(); });
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
        ACADEMY.motto + ' 创立：' + ACADEMY.founded + '。' + ACADEMY.admission + '。点击下方「星槎学院」标签，看四院与分选礼的完整记录。';
      card.classList.add('open');
      return;
    }
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
        var tone = /宿敌|世仇|敌对|憎恶|北征|恐惧|偷/.test(rel[1])
          ? 'hostile' : (/友善|盟友|互敬|血誓|主顾/.test(rel[1])
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
        bar('耗光', r.st['耗光']) + bar('记账', r.st['记账']) + bar('惜年', r.st['惜年']) +
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

  /* ---------------- 星槎学院：动态注入 ---------------- */

  var A = ACADEMY;
  var statsRow = document.getElementById('academy-stats-row');
  if (statsRow) {
    statsRow.innerHTML =
      '<div><span>创立</span><b>' + A.founded + '</b></div>' +
      '<div><span>升船</span><b>' + A.lifted + '</b></div>' +
      '<div><span>校长</span><b>' + A.head + '</b></div>' +
      '<div><span>入学</span><b>' + A.admission + '</b></div>';
  }

  function houseSigil(id) {
    if (id === 'dawn') return '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2"><rect x="18" y="14" width="28" height="36" rx="2"/><path d="M24 50 V58 M40 50 V58"/><path d="M32 22 L32 38"/><circle cx="32" cy="20" r="4" fill="currentColor" stroke="none"/></svg>';
    if (id === 'speak') return '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 16 H48 M16 28 H40 M16 40 H44 M16 52 H28"/></svg>';
    if (id === 'forge') return '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 40 H52 L46 48 H18 Z"/><path d="M24 40 V22 H40 V40"/><path d="M20 22 H44"/></svg>';
    return '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="32" cy="44" rx="18" ry="8"/><path d="M32 16 V36"/><circle cx="32" cy="16" r="5"/></svg>';
  }

  function showInspect(b) {
    if (!b) return;
    var n = document.getElementById('ac-name');
    var d = document.getElementById('ac-desc');
    if (n) n.textContent = b.name;
    if (d) d.textContent = b.desc;
  }

  if (window.AcademyView) {
    AcademyView.onPick(function (b) { if (b) showInspect(b); });
  }
  var btns = document.getElementById('ac-building-btns');
  if (btns && A.buildings) {
    var bh = '';
    for (var bi = 0; bi < A.buildings.length; bi++) {
      var bd = A.buildings[bi];
      bh += '<button class="ac-pin" data-id="' + bd.id + '">' + bd.name + '</button>';
    }
    btns.innerHTML = bh;
    var pins = btns.querySelectorAll('.ac-pin');
    for (var pj = 0; pj < pins.length; pj++) {
      (function (btn) {
        btn.addEventListener('click', function () {
          var id = btn.getAttribute('data-id');
          for (var k = 0; k < A.buildings.length; k++) {
            if (A.buildings[k].id === id) showInspect(A.buildings[k]);
          }
          if (window.AcademyView) AcademyView.flyTo(id);
        });
      })(pins[pj]);
    }
  }
  var dayBtn = document.getElementById('btn-ac-day');
  var nightBtn = document.getElementById('btn-ac-night');
  if (dayBtn) dayBtn.addEventListener('click', function () {
    if (window.AcademyView) AcademyView.setNight(false);
    dayBtn.classList.add('active'); if (nightBtn) nightBtn.classList.remove('active');
  });
  if (nightBtn) nightBtn.addEventListener('click', function () {
    if (window.AcademyView) AcademyView.setNight(true);
    nightBtn.classList.add('active'); if (dayBtn) dayBtn.classList.remove('active');
  });
  if (nightBtn) {
    nightBtn.classList.add('active');
    if (window.AcademyView) AcademyView.setNight(true);
  }


  var histEl = document.getElementById('academy-history');
  if (histEl) {
    var hh = '';
    for (var hi = 0; hi < A.history.length; hi++) {
      hh += '<p' + (hi === 0 ? ' class="dropcap"' : '') + '>' + A.history[hi] + '</p>';
    }
    histEl.innerHTML = hh;
  }

  var houseEl = document.getElementById('house-grid');
  if (houseEl) {
    var hh2 = '';
    for (var hj = 0; hj < A.houses.length; hj++) {
      var hs = A.houses[hj];
      hh2 +=
        '<article class="house-card" style="--hc:' + hs.color + '">' +
        '<div class="house-emblem" style="color:' + hs.color + '">' + houseSigil(hs.id) + '</div>' +
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
        '<div class="house-foot">' +
        '<div><b>开院</b>' + hs.founded + '</div>' +
        '<div><b>名士</b>' + hs.alumni + '</div>' +
        '</div>' +
        '</article>';
    }
    houseEl.innerHTML = hh2;
  }

  var sortEl = document.getElementById('academy-sorting');
  if (sortEl) sortEl.textContent = A.sorting.desc;

  var ritEl = document.getElementById('academy-rituals');
  var bldEl = document.getElementById('academy-buildings');
  if (ritEl) {
    var rh = '';
    for (var rti = 0; rti < A.rituals.length; rti++) {
      rh += '<div class="academy-item"><h5>' + A.rituals[rti].name + '</h5><p>' + A.rituals[rti].desc + '</p></div>';
    }
    ritEl.innerHTML = rh;
  }
  if (bldEl) {
    var bh = '';
    for (var bli = 0; bli < A.buildings.length; bli++) {
      bh += '<div class="academy-item"><h5>' + A.buildings[bli].name + '</h5><p>' + A.buildings[bli].desc + '</p></div>';
    }
    bldEl.innerHTML = bh;
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
