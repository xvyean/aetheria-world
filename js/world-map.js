/* 艾瑟兰舆图 · 纯 DOM 交互图（v5）—— 三大陆 + 势力 + 城（44 个点位，含"多出来的点"） */
(function () {
  'use strict';

  var POINTS = [
    // 势力主城（大点）
    { n:'白冠城',  f:'白冠王国', x:38, y:30, big:1 },
    { n:'灰港城',  f:'灰港公国', x:20, y:45, big:1 },
    { n:'晨晖城',  f:'晨晖主教区', x:30, y:52, big:1 },
    { n:'银叶王庭', f:'银叶', x:62, y:38, big:1 },
    { n:'玄境城',  f:'月影', x:70, y:20, big:1 },
    { n:'熔心城',  f:'熔心城邦', x:14, y:68, big:1 },
    { n:'铜脊堡',  f:'铜脊部族', x:8, y:82, big:1 },
    { n:'黑牙堡',  f:'黑牙', x:80, y:58, big:1 },
    { n:'沼鼓营',  f:'血誓', x:87, y:66, big:1 },
    { n:'金麦镇',  f:'金麦谷', x:46, y:64, big:1 },
    { n:'麦浪广场', f:'麦浪商盟', x:52, y:72, big:1 },
    { n:'碎浪港',  f:'碎浪群岛', x:78, y:82, big:1 },
    { n:'无影城',  f:'暮影领', x:55, y:6, big:1 },
    { n:'星辉圣所', f:'圣所', x:47, y:23, big:1 },
    // 其余城（小点）
    { n:'云锦城', f:'白冠王国', x:42, y:26 }, { n:'桥头镇', f:'白冠王国', x:44, y:36 },
    { n:'盐滩港', f:'灰港公国', x:24, y:40 }, { n:'雾台港', f:'灰港公国', x:16, y:50 },
    { n:'圣泉镇', f:'晨晖/圣所', x:40, y:48 }, { n:'垂柳村', f:'银叶', x:64, y:34 },
    { n:'羡音镇', f:'银叶', x:58, y:44 }, { n:'荫露阁', f:'月影', x:66, y:14 },
    { n:'月石镇', f:'月影', x:74, y:16 }, { n:'垂云村', f:'暮影领', x:52, y:12 },
    { n:'七岭堡', f:'熔心城邦', x:18, y:62 }, { n:'铜涧镇', f:'熔心城邦', x:24, y:72 },
    { n:'五江堡', f:'铜脊部族', x:12, y:88 }, { n:'二爿村', f:'铜脊部族', x:20, y:84 },
    { n:'雷岗堡', f:'铜脊部族', x:5, y:76 }, { n:'古峡营', f:'黑牙', x:76, y:64 },
    { n:'百珊营', f:'血誓', x:90, y:72 }, { n:'苍芦村', f:'血誓', x:82, y:74 },
    { n:'小麦镇', f:'金麦谷', x:40, y:60 }, { n:'老玥村', f:'金麦谷', x:36, y:68 },
    { n:'登阁巷', f:'麦浪商盟', x:56, y:68 }, { n:'钱巷', f:'麦浪商盟', x:48, y:76 },
    { n:'岘礁港', f:'碎浪群岛', x:72, y:86 }, { n:'风读村', f:'碎浪群岛', x:84, y:78 },
    { n:'白烛镇', f:'晨晖主教区', x:34, y:55 }, { n:'雾渡镇', f:'月影', x:72, y:25 },
    { n:'白鲸镇', f:'暮影领', x:48, y:9 }, { n:'寂灭之塔', f:'暮影领', x:57, y:2 },
    // 第 43 个点（舆图的谜）
    { n:'？？？', f:'舆图上的第 43 点', x:47, y:23.6, ghost:1 }
  ];

  var map = document.getElementById('map');

  // 大陆剪影（SVG 简化形状）
  var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 100 100');
  svg.style.position = 'absolute'; svg.style.inset = '0';
  svg.innerHTML =
    '<path d="M30 18 L44 8 L58 12 L72 8 L80 18 L78 28 L88 40 L84 56 L92 68 L84 84 L70 90 L54 84 L44 92 L30 86 L20 72 L26 58 L16 46 L22 30 Z" fill="#1e2416" stroke="#39422a"/>' +
    '<path d="M6 62 L14 58 L18 66 L12 74 L4 70 Z" fill="#241f12" stroke="#3c3422"/>' +
    '<path d="M66 90 L74 86 L80 92 L72 96 Z" fill="#171b22" stroke="#2c3644"/>' +
    '<path d="M50 0 L58 4 L52 10 L44 6 Z" fill="#101418" stroke="#2a3442"/>' +
    '<ellipse cx="47" cy="21" rx="3.2" ry="6" fill="#bfefff" opacity=".16"/>' +
    '<ellipse cx="47" cy="21" rx="1.4" ry="4.4" fill="#bfefff" opacity=".5"/>' +
    '<circle cx="47" cy="12" r="1.0" fill="#bfefff" opacity=".8"/>';  // 星槎（裂隙上方）
  map.appendChild(svg);

  POINTS.forEach(function (p, i) {
    var d = document.createElement('button');
    d.className = 'pt' + (p.big ? ' big' : '') + (p.ghost ? ' ghost' : '');
    d.style.left = p.x + '%'; d.style.top = p.y + '%';
    d.innerHTML = '<i></i><span>' + p.n + '</span>';
    d.dataset.i = i;
    d.addEventListener('click', function () { showHint(p); });
    map.appendChild(d);
  });

  var hint = document.createElement('div');
  hint.className = 'hint hidden';
  map.appendChild(hint);
  function showHint(p) {
    hint.innerHTML = '<b>' + p.n + '</b><span>' + (p.f || '') + '</span>' +
      (p.ghost ? '<em>舆图 412 版把它画在裂隙正中。星语院 399 年勘过："多出的点，是纸自己画的。"</em>' : '');
    hint.classList.remove('hidden');
    setTimeout(function () { hint.classList.add('hidden'); }, 3200);
  }

  // 图例
  var legend = document.getElementById('legend');
  var groups = {};
  POINTS.forEach(function (p) { if (!p.ghost) groups[p.f] = (groups[p.f] || 0) + 1; });
  legend.innerHTML = Object.keys(groups).map(function (k) {
    return '<span class="lg"><b>' + k + '</b> ' + groups[k] + ' 城</span>';
  }).join('') + '<span class="lg ghost"><b>？</b> 第 43 点</span>';

  // 四院速览
  document.getElementById('mini-houses').innerHTML = HOUSES.map(function (h) {
    return '<div class="mh" style="--hc:' + h.color + '"><b>' + h.name + '</b>' +
      '<span>光，用来——' + h.answer + '</span><em>“' + h.motto + '”</em></div>';
  }).join('');

  document.getElementById('mini-mysteries').innerHTML = MYSTERIES.map(function (m) {
    return '<li><b>#' + m.n + ' · ' + m.t + '</b><span>' + m.q + '</span></li>';
  }).join('');
})();
