/* ============================================================
 * 星槎学院 · 设定圣经（新）渲染引擎
 * 数据源：bible/ 目录（01-06 卷），此处提取为网页摘要。
 * ============================================================ */

var BIBLE = {
  volumes: [
    { no: '01', title: '世界之骨 · 底层规则', file: 'bible/00-世界之骨.md',
      desc: '星辉是债务不是能量；心焰、烬人、浮空的"还重说"；历法无日月；十字以内星槎免费。',
      points: ['星辉=光的伤口','心焰1/12可见','岛底无鸟','正午不宜发誓'] },
    { no: '02', title: '星槎学院总志', file: 'bible/01-星槎学院总志.md',
      desc: '学院是仲裁所、气象站、翻译局、银行、监狱、赌场、码头；四席会与烛守局；岛规十三条；人物录。',
      points: ['四席会','岛规十三条','坟市','分选礼春分夜'] },
    { no: '03', title: '四院谱', file: 'bible/02-四院谱.md',
      desc: '晨辉=序、星语=删、锤音=誓、海心=潮。四院建筑风格与院训一体。',
      points: ['启 言 锻 怀','抱柱四学徒','星斗赛院际清算'] },
    { no: '04', title: '空岛建筑志', file: 'bible/03-空岛建筑志.md',
      desc: 'Blender 施工说明书：星陨塔、星穗馆、四院、宿舍环21+1、山门、钟楼、浮池。',
      points: ['塔高34','穹顶带开缝','第22栋缺席','浮池满而不溢'] },
    { no: '05', title: '大事件与新历412年', file: 'bible/04-大事记与新历412年.md',
      desc: '由纪元前3000年到星辉历412年的全部可考编年；及此年秋的世界动态表。',
      points: ['白冠之誓','空岛升腾','影蚀之灾','潮汐提前'] },
    { no: '06', title: '飞升之卷 · 十个谜', file: 'bible/05-飞升之卷.md',
      desc: '谜是用来让世界有余地的，不是用来答题的。813斤、第22栋、回声井、会挪书的书……',
      points: ['谜一 813斤','谜二 缺席宿舍','谜四 裂隙晶的答案','谜十 校长等谁'] },
    { no: '07', title: '术语与设定审计', file: 'bible/06-术语与设定审计.md',
      desc: '术语词典 + 新旧设定审计：本次重写对旧版 v3 的每一条修正及其原因。',
      points: ['紫禁于学院','金=最贵的光','分选礼改期'] }
  ],
  rules: [
    '岛上不许施影语。', '岛上不许叫醒别人的心焰。', '黄昏钟响后，不许出岛。',
    '星穗馆七层，非经烛守局不得入。', '浮池里不许捞"星影"。', '不许给裂隙晶起名字。',
    '不许在回廊上跑。', '锤音院的炉子外人不得碰。', '岛上不许决斗——矛盾写到白板墙上，写下的必须是真的。',
    '无名日不许提任何人的名字。', '不许把岛上的石头带下岛。', '沉钟不许敲第三下。',
    '星潮夜，四院同席，席上不许提胜负。'
  ],
  people: [
    ['凯兰·星羽', '校长', '在任第九十一年。每年只批四行字。从不离岛，从不睡觉，也不死。谜十。'],
    ['席恩·白冠', '晨辉院长', '正统派。主张学院该下山。每年提案一次，被否一次。绰号"布告"。'],
    ['露弥·瑟兰', '星语院长', '怀疑派。221 岁。教"删"教到只剩七个字。常言：我们不知道的事，比书多。'],
    ['巴林·铁砧', '锤音院长', '务实派。靠辉纹许可填平学院一半的账。和露弥吵了 40 年。'],
    ['柯蕾塔·碎浪', '海心院长', '自由派。去过暮影海峡边缘一次，回来撕了日志最后一页。全院唯一抽烟的人。'],
    ['纳里·银槌', '秤官', '在任 29 年，绰号"年年少八百斤"。他称的是岛。'],
    ['沈砚', '烛守', '烬人。过目不忘，从不直视任何人。管全部档案与年册。'],
    ['哑钟', '钟守', '种族与年龄不祥。从不出声，但听得见。用鼓点报时。'],
    ['顾言', '删书人', '管"被删到只剩七个字的原稿"。自己说话也不超过七个字。'],
    ['苔婶', '园丁', '半身人，139 岁。全院最老的梧桐是她祖母种的。'],
    ['芹姑', '药婆', '全岛唯一的医生。药房在"15 栋"——一个不存在的编号。'],
    ['栓子', '缆索匠', '管吊篮泊位。全校唯一敢坐吊篮时睁眼的人。']
  ],
  mysteries: [
    ['谜一 · 813 斤', '秤室的铜牌：岛较上年轻 813 斤。轻得非匀速；星辉历 400 年反而重 220 斤。岛在称什么？'],
    ['谜二 · 缺席的宿舍', '图纸 22 栋，现场 21 栋。第 22 栋的位置有一圈旧地基石，比别处深。半身人住进了不存在的位置。'],
    ['谜三 · 回声井', '星陨塔第一层的井。向下喊，回上来的是别人的声音。402 年那夜，无人认领。'],
    ['谜四 · 裂隙晶的问题', '被问 66 次的是"你最怕失去什么"。但 66 个答案，一次也没被抄下来。'],
    ['谜五 · 会挪书的书', '星穗馆七层，一本没有书名的书。它会自己挪位置。顾言的陈述："书挪。人找。没找到过。"'],
    ['谜六 · 提前的四十年', '纪元前 620 年潮汐早到 40 年，台地升空。412 年纹路再宽——距上次恰好 1032 年。'],
    ['谜七 · 第 211 号自荐生', '自荐入学者 211 人，1 人成"最坏的记录"：341 年入，345 年出。原因：不可载。'],
    ['谜八 · 擦不掉的锈', '钟身的海锈。擦掉的地方，第二天长出形状一模一样的锈。哑钟试过 19 次。'],
    ['谜九 · 第 41 片水晶', '圣所现存 411 片水晶。目录记 412 片——第 41 片（371 年）登记在册，实物失踪。'],
    ['谜十 · 校长在等谁', '404 年冬至夜（无日月），值夜学生看见校长独自站在山门，朝地面，站了很久。']
  ]
};

/* ---------------- 注入引擎 ---------------- */
(function () {
  if (typeof window === 'undefined') return;
  var A = (typeof ACADEMY !== 'undefined') ? ACADEMY : null;
  function $(id) { return document.getElementById(id); }

  document.addEventListener('DOMContentLoaded', function () {
    if (!A) return;
    $('academy-motto').textContent = '“' + A.motto + '”';
    $('academy-founded').textContent = A.founded;
    $('academy-lifted').textContent = A.lifted;
    $('academy-head').textContent = A.head;
    $('academy-admit').textContent = A.admission;

    var hist = $('academy-history');
    if (hist) {
      hist.innerHTML = A.history.map(function (h, i) {
        return '<p' + (i === 0 ? ' class="dropcap"' : '') + '>' + h + '</p>';
      }).join('');
    }

    var grid = $('house-grid');
    if (grid) {
      var imgMap = { dawn: 'house-dawn.png', speak: 'house-speak.png', forge: 'house-forge.png', tide: 'house-tide.png' };
      grid.innerHTML = A.houses.map(function (h) {
        return '<article class="house-card" style="--hc:' + h.color + '">' +
          '<div class="house-emblem"><img src="img/' + (imgMap[h.id] || '') + '" alt="' + h.sigil + '徽记"></div>' +
          '<div class="house-head"><h3>' + h.name + '</h3><p class="house-motto">“' + h.motto + '”</p></div>' +
          '<div class="house-tags"><span>学派 · ' + h.element + '</span><span>院德 · ' + h.virtue + '</span><span>徽记 · ' + h.sigil + '</span></div>' +
          '<p class="house-desc">' + h.desc + '</p>' +
          '<div class="house-foot"><div><b>开院</b>' + h.founded + '</div><div><b>名士</b>' + h.alumni + '</div></div>' +
          '</article>';
      }).join('');
    }

    var sortEl = $('academy-sorting');
    if (sortEl) sortEl.innerHTML = '<span class="dropcap">分</span>' + A.sorting.desc.replace(/^分/, '');

    var rules = $('rules-list');
    if (rules) rules.innerHTML = '<ol>' + BIBLE.rules.map(function (r) {
      return '<li>' + r + '</li>';
    }).join('') + '</ol>';

    var rit = $('academy-rituals'), bld = $('academy-buildings');
    if (rit) rit.innerHTML = A.rituals.map(function (x) { return '<div class="academy-item"><h5>' + x.name + '</h5><p>' + x.desc + '</p></div>'; }).join('');
    if (bld) bld.innerHTML = A.buildings.map(function (x) { return '<div class="academy-item"><h5>' + x.name + '</h5><p>' + x.desc + '</p></div>'; }).join('');

    var people = $('people-list');
    if (people) people.innerHTML = BIBLE.people.map(function (p) {
      return '<div class="people-card"><b>' + p[0] + '</b><span>' + p[1] + '</span><p>' + p[2] + '</p></div>';
    }).join('');

    var mys = $('mysteries-list');
    if (mys) mys.innerHTML = BIBLE.mysteries.map(function (m) {
      return '<div class="academy-item mystery"><h5>' + m[0] + '</h5><p>' + m[1] + '</p></div>';
    }).join('');

    /* ---- 世界观 tab ---- */
    var W = (typeof WORLD !== 'undefined') ? WORLD : null;
    if (W) {
      $('lore-name').textContent = W.name;
      $('lore-en').textContent = W.en + ' · ' + W.subtitle;
      $('lore-epigraph').textContent = W.epigraph;
      $('lore-epigraph-source').textContent = W.epigraphSource;
      $('lore-year').textContent = W.year + ' · ' + W.tagline;
    }
    var mg = $('school-grid');
    if (mg && typeof MAGIC !== 'undefined') {
      mg.innerHTML = MAGIC.schools.map(function (s) {
        return '<div class="mini-card" style="--sc:' + s.color + '"><b>' + s.name + '</b><span>' + s.who + '</span><p>' + s.desc + '</p></div>';
      }).join('');
    }
    var ch = $('chronicle-list');
    if (ch && typeof CHRONICLE !== 'undefined') {
      ch.innerHTML = CHRONICLE.map(function (c) {
        return '<div class="chronicle-row"><span class="era">' + c.era + '</span><div><b>' + c.title + '</b><i>' + c.year + '</i><p>' + c.desc + '</p></div></div>';
      }).join('');
    }
    var ar = $('artifact-list');
    if (ar && typeof ARTIFACTS !== 'undefined') {
      ar.innerHTML = ARTIFACTS.map(function (a) {
        return '<div class="mini-card"><b>' + a.name + '</b><span>' + a.race + '</span><p>' + a.desc + '</p></div>';
      }).join('');
    }
    var gl = $('glossary-table');
    if (gl && typeof GLOSSARY !== 'undefined') {
      gl.innerHTML = '<div class="glossary">' + GLOSSARY.map(function (g) {
        return '<div class="g-row"><b>' + g[0] + '</b><span>' + g[1] + '</span></div>';
      }).join('') + '</div>';
    }
    var geo = $('geo-grid');
    if (geo && typeof GEOGRAPHY !== 'undefined') {
      geo.innerHTML = GEOGRAPHY.map(function (g) {
        return '<div class="mini-card" style="--sc:' + g.color + '"><b>' + g.name + '</b><span>' + g.who + '</span><p>' + g.desc + '</p></div>';
      }).join('');
    }

    /* ---- 圣经 tab ---- */
    var bl = $('bible-list');
    if (bl) {
      bl.innerHTML = BIBLE.volumes.map(function (v) {
        return '<div class="bible-vol"><div class="bv-no">' + v.no + '</div><div class="bv-body"><h4>' + v.title + '</h4><code>' + v.file + '</code><p>' + v.desc + '</p><div class="bv-tags">' +
          v.points.map(function (p) { return '<span>' + p + '</span>'; }).join('') + '</div></div></div>';
      }).join('');
    }

    /* ---- 资产 tab ---- */
    var al = $('asset-list');
    if (al) {
      al.innerHTML = [
        ['models/academy.glb', '星槎学院精细三维资产（83,843 面 · 17 分区 · 全材质）'],
        ['models/academy.blend', 'Blender 源工程（可打开继续编辑）'],
        ['blender/build.py', '一键构建管线：blender/build.py --build / --render / --export'],
        ['renders/', '六机位 x 三氛围 渲染成品（暮潮 / 晨辉 / 星夜）'],
        ['bible/', '设定圣经七卷（世界之骨 / 总志 / 四院谱 / 建筑志 / 大事记 / 飞升之卷 / 审计）']
      ].map(function (a) {
        return '<div class="mini-card asset"><b>' + a[0] + '</b><span>' + a[1] + '</span></div>';
      }).join('');
    }

    /* ---- tab 切换 ---- */
    var tabs = document.querySelectorAll('.tab');
    tabs.forEach(function (t) {
      t.addEventListener('click', function () {
        tabs.forEach(function (x) { x.classList.remove('active'); });
        t.classList.add('active');
        document.querySelectorAll('.tabpane').forEach(function (p) { p.classList.remove('active'); });
        var pane = $('tab-' + t.getAttribute('data-tab'));
        if (pane) pane.classList.add('active');
      });
    });
  });
})();
