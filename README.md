<div align="center">

# 艾瑟兰

**一颗未死的星 · 一条未落的船**

`Three.js` · `Blender` · `程序化大陆` · `星槎学院 GLB`

</div>

---

> “光不是祝福。光是一笔还不上的账。”
> ——卫晚潮，星槎学院第十九任校长，熄灯钟下

海里躺着一颗没死完的星。世上所有的法术，都是在花它还没散尽的热。花得越多，这颗星死得越快。

**星槎不是学校。** 它是八百年前没捞到这颗星的那条船——停在热气上，一直没落下来。船上的人后来开始教后来的人两件事：怎么少花一点，以及怎么把花掉的每一星都记下来。

完整设定见 [`lore/WORLD.md`](lore/WORLD.md)。网页上的《余光备忘》是它的摘录。

---

## 这一版改了什么

- **设定推倒重写。** 不再是女神大战虚空之蛇 + 霍格沃茨四院。四院是四个答案（花掉 / 写成字 / 打进铁里 / 还回海里），分选问的是“这一年的光你要花在什么上”，暮影是还清了贷因此不再投下影子的人。
- **学院用 Blender 重做。** `blender/build_academy.py` 生成船岛：账桅、四院、退字阁、浮池、余年盘、旧艏。导出 `models/academy.glb`，在世界地图和学院页里各加载一次。
- **学院页是可点的 3D 视口。** 点建筑看志，昼 / 暮切换。
- 三块大陆、十四势力、四十二城的地图还在，文案全部按新设定重写。

## 本地运行

无需构建：

```bash
python3 -m http.server 8080
# 打开 http://localhost:8080
```

> Three.js r128 与 GLTFLoader 已内置于 `vendor/`。**必须用静态服务器打开**，否则 `academy.glb` 会被浏览器拦住。
> 建议桌面端 Chrome / Edge / Firefox。

## 重新生成学院模型

需要本机 Blender 4.x：

```bash
blender --background --factory-startup --python blender/build_academy.py
```

产物：`models/academy.glb`、`blender/academy.blend`、`img/academy-hero.png`。

## 目录

```
aetheria-world/
├── index.html
├── lore/WORLD.md          # 设定全文
├── blender/
│   ├── build_academy.py   # 船岛生成脚本
│   └── academy.blend
├── models/academy.glb
├── css/style.css
├── js/
│   ├── data.js            # 世界观
│   ├── world.js           # 大陆引擎 + 加载 GLB
│   ├── academy-view.js    # 学院独立视口
│   ├── terrain.js
│   ├── noise.js
│   └── app.js
└── vendor/                # three + OrbitControls + GLTFLoader
```

## 许可

[MIT License](./LICENSE)
