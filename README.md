<div align="center">

# 艾瑟兰 · AETHERIA

**一颗未死的星 · 一条未落的船**

`Blender 程序化建模` · `Three.js 查看器` · `设定圣经驱动` · `星辉历 412 年`

</div>

> “光不是祝福。光是一笔还不上的账。”
> ——卫晚潮，星槎学院第十九任校长，熄灯钟下

海里躺着一颗没死完的星。世上所有的法术，都是在花它还没散尽的热。花得越多，这颗星死得越快。

**星槎不是学校。** 它是八百年前没捞到这颗星的那条船——停在热气上，一直没落下来。船上的人后来开始教后来的人两件事：怎么少花一点，以及怎么把花掉的每一星都记下来。

---

## v5 重构 · 这一版改了什么

| 维度 | 旧版（v4） | 重构版（v5） |
|---|---|---|
| 设定 | 七卷圣经，但纪年混乱（星辉历/星辉历并存） | **设计宪法 + 九卷圣经**：`docs/DESIGN.md` 立规矩；纪年统一为 **星辉历**；新增《学院生活志》《世界舆图志》；十谜加厚（已知/异常/三说） |
| README | 残留未解决的 git 冲突标记（`<<<<<<< HEAD`） | 完全重写（本文件） |
| 管线 | `blender/engine` 单文件脚本，无贴图 | **`blender/pipeline` 分区分层管线**：`texgen.py`（22 张程序化可平铺贴图）→ `geo.py`（几何库）→ `city/`（17 个分区施工）→ `assemble`（总装）→ `qa`（质检）→ `cameras`（机位×氛围）→ GLB 导出 |
| 建模 | 玩具级低模 | 17 分区 / ~2800 对象 / ~93k+ 三角面 / 50+ 材质：四院、回廊（半墙滚书·无锁半开门）、星陨塔（观星环廊·可开铜穹·裂隙晶）、浮池（悬出岛缘的镜面水）、星穗馆（24 金肋金穹）、宿舍环（21+1，第 15 号位的灯下黑）、山门（吊篮·白板墙·守门石像）、钟楼（海锈沉钟）、长桌堂（欠账榜）、白石浴场（晾衣绳）、名士墓（27 碑·3 块新擦）、以及全岛 29 棵树 / 40 丛灌木 / 60 簇花 / 14 盏石灯笼 |
| 渲染 | 六机位×三氛围 | 九机位×三氛围（暮潮/晨辉/星夜），Cycles 输出；含世界场景机位（裂隙光柱+灰港灯火+海面） |
| 网页 | 学院页 + 旧世界页 | **学院手册页**（`academy.html`：3D 查看器可点建筑看志 + 四院/十谜/岛规/人物/世界五页签，GLB 加载失败自动降级平面图）+ **世界舆图页**（`world-modern.html`：三维度势力城点图，含“第 43 个点”的谜） |

## 版本谱系

`main` 只承载整理、验证过的综合版——即当前 v5。历史上的创作路线已按用户（xvyean）的整理拆分为独立分支，互不覆盖：

| 分支 | 内容 | 基线 |
| --- | --- | --- |
| [`version/v1-original`](https://github.com/xvyean/aetheria-world/tree/version/v1-original) | 最初的单大陆 3D 奇幻世界 | `f92382c` |
| [`version/v2-expanded-world`](https://github.com/xvyean/aetheria-world/tree/version/v2-expanded-world) | 三河两湖、十四势力的大陆级扩展 | `28e59a8` |
| [`version/v3-three-continents`](https://github.com/xvyean/aetheria-world/tree/version/v3-three-continents) | 三块大陆、四十二城、初版星槎学院 | `1e34911` |
| [`version/v4-afterglow`](https://github.com/xvyean/aetheria-world/tree/version/v4-afterglow) | 《余光未尽》设定与船岛 GLB | `b43fde1` |
| [`version/v4-blender-academy`](https://github.com/xvyean/aetheria-world/tree/version/v4-blender-academy) | 独立 Blender 4.2 / Draco 学院方案 | `7ac41da` |
| [`version/v4-modern-bible`](https://github.com/xvyean/aetheria-world/tree/version/v4-modern-bible) | v4 综合版快照（v5 之前的 main 状态） | `7ba3531` |

完整的分支来源、选择建议与恢复方法见 [`VERSIONING.md`](VERSIONING.md)；给 AI 贡献者的仓库守则见 [`AGENTS.md`](AGENTS.md)——不直接在主分支开新方向、不提交冲突标记、提交前跑冲突检查与 `node --check`。

## 这是什么世界

- **世界是一本账，不是一场战争。** 星辉（Aether）不是能量，是“光的状态”——星辰碎片坠海时留下的伤口，至今在渗光。一切魔法都是借光：以心焰为烛，引裂隙的光，**用了要还**。
- **四院是四个答案**：花掉（晨辉）／写成字（星语）／打进铁里（锤音）／还回海里（海心）。分选礼问的不是“你适合什么”，是“**这一年的光，你要花在什么上**”。
- **学院是台地上的仲裁所、翻译局、专利局、银行、监狱、赌场和码头**（大多现在还当着）。六族送学生来，是求学，也是交人质。
- **十谜只留问法**：813 斤、缺席的宿舍、回声井、裂隙晶的问题、会挪书的书、提前的四十年、第 211 号自荐生、擦不掉的锈、第 41 片水晶、校长在等谁。
- **此刻（412 年秋）**：大潮或提前到 413 年春；裂隙纹路十年宽了“两指”；雾线南移三十里；矿价暴涨；血誓百年续誓将至；金麦谷丰收却囤粮；一位观察员带着一只很轻的匣子上了岛——校长 91 年来第一次批准圣所请求。

完整设定见 `bible/`（九卷）与 `docs/DESIGN.md`（设计宪法）。网页 `academy.html` / `world-modern.html` 是它的摘录与交互版。

## 快速开始

### 网页版（需本地静态服务器加载 GLB）

```bash
cd aetheria-world
python3 -m http.server 8899
# 浏览器打开
#   http://localhost:8899/academy.html      # 学院 · 3D 手册
#   http://localhost:8899/world-modern.html # 世界 · 舆图
```

> three.js r128 与 GLTFLoader 已内置于 `vendor/`。**必须用静态服务器打开**，否则 `academy.glb` 会被浏览器拦截。
> 若 GLB 未能加载，学院页会自动降级为可交互的平面学院图（内容完整，只是没有 3D）。

### 重新生成模型

需要 Blender 4.x：

```bash
# 1) 生成程序化贴图（纯 numpy，可用系统 python3 运行）
python3 blender/pipeline/texgen.py

# 2) 构建学院（保存 models/academy.blend + 质检报告）
blender -b -noaudio --python blender/build.py -- --build --qa

# 3) 渲染（9 机位 × 3 氛围，输出 renders/）
blender -b -noaudio --python /path/to/your_render_script.py   # 见 blender/README 说明，或：
blender -b -noaudio --python blender/build.py -- --render --shot hero_dusk --samples 64 --res 1440x900

# 4) 导出 GLB（学院 + 世界两个资产）
blender -b -noaudio --python blender/build.py -- --export
```

> 渲染为 Cycles CPU（无需 GPU）；建议 `--samples 64`、`--res 1440x900`。

## 目录

```
aetheria-world/
├── README.md              # 本文件
├── docs/DESIGN.md         # ★ 设计宪法（信条/反 AI 味清单/建造规范）
├── TIME.md                # 进度与耗时台账
├── bible/                 # ★ 设定圣经（九卷）
│   ├── 00-世界之骨.md            # 星辉=借来的光 · 裂隙 · 历法 · 死亡与影子
│   ├── 01-星槎学院总志.md        # 学院是什么 · 四席会 · 岛规十三条 · 人物
│   ├── 02-四院谱.md              # 四个答案 · 四合院脾气
│   ├── 03-空岛建筑志.md          # = Blender 施工说明书（方位/尺寸/材质/第二功能）
│   ├── 04-大事记与新历412年.md   # 从大星陨到 412 年秋的世界动态表
│   ├── 05-飞升之卷.md            # 十谜（已知/异常/三说 · 加厚版）
│   ├── 06-术语与设定审计.md      # 术语词典 + 反 AI 味清单 + v5 差异审计
│   ├── 07-学院生活志.md          # ★新：一天/一年/星记/忌讳（学校也要吃饭洗澡）
│   └── 08-世界舆图志.md          # ★新：大陆 · 六族 · 四十二城（含第 43 点之谜）
├── blender/
│   ├── build.py           # CLI：--build / --render / --export / --qa
│   └── pipeline/
│       ├── util.py        # 调色板/随机种子/集合命名
│       ├── layout.py      # ★ 全岛布局常量表（圣经↔几何的唯一对接点）
│       ├── texgen.py      # ★ 程序化可平铺贴图（纯 numpy → PNG）
│       ├── mats.py        # 材质工厂（50+ 种：贴图+PBR+自发光）
│       ├── geo.py         # 几何库（手动网格+自动UV，无布尔）
│       ├── island.py      # 岛体：四带岩层/船首岬/晶簇/垂蔓/浮岩
│       ├── city/          # 17 个分区施工（塔/广场/回廊/四院/馆/宿舍环/山门/钟楼/长桌堂/浴场/墓园/植被...）
│       ├── assemble.py    # 总装
│       ├── cameras.py     # 9 机位 × 3 氛围（灯光组）
│       ├── qa.py          # 质检（面数/材质/UV/禁紫/水面平度）
│       ├── worldscene.py  # 世界场景（裂隙光柱/海面/灰港灯火/远山）
│       └── export_glb.py  # GLB 导出
├── models/
│   ├── academy.blend      # Blender 工程
│   ├── academy.glb        # 学院资产（17 分区 · 贴图随包）
│   └── world.glb          # 含世界场景版本
├── assets/textures/       # 22 张程序化贴图（512² 可平铺）
├── renders/               # 九机位 × 三氛围 成品
├── academy.html           # ★ 学院手册（3D 查看器 + 设定五页签）
├── world-modern.html      # ★ 世界舆图（势力城点图 + 第 43 点之谜）
├── index.html             # 旧版世界地图（世界观 v3，保留作对比）
├── css/  js/  vendor/  tools/
└── TIME.md
```

## 设计自检（反 AI 味）

写设定 / 建模前必查（详见 `bible/06` 第二节与 `docs/DESIGN.md`）：

1. 出现“星辉历” → 改“星辉历”。
2. 学院出现紫色（海心花圃除外） → 改。
3. 建筑数 ≠《建筑志 v2》 → 改。
4. 分选礼 ≠ 试读年次年春分夜 → 改。
5. 十谜“给出了答案” → 收回，只留问法。
6. 金色出现在星陨塔（穹肋/圆窗框）与星穗馆（金肋/金穗）以外 → 改。
7. 删掉奇幻词汇后只剩空话的段落 → 重写。

## 许可

MIT（保留原 LICENSE）。
